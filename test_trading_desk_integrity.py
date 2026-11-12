"""
Comprehensive System & Unit Test Suite for Human-Like Trading Desk & Workforce 2.0.
Verifies all 7 deliverables: Database Schema, Journal Logging, Risk Manager with Kill Switch,
Specialist Agents, Decision Desk Consensus, Backtester with Walk-Forward, and Reporting.
"""

import unittest
import os
import sys
import shutil
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timezone

from app.data.db_manager import DatabaseManager
from app.data.data_collector import DataCollector
from app.learning.journal import TradeJournal
from app.trading.risk_manager import RiskManager
from app.agents.trend_agent import TrendAnalyst
from app.agents.momentum_agent import MomentumAnalyst
from app.agents.liquidity_agent import LiquidityAnalyst
from app.agents.session_agent import SessionVolatilityAnalyst
from app.agents.sentiment_agent import SentimentAnalyst
from app.agents.decision_desk import DecisionDesk
from app.validation.backtester import WalkForwardBacktester
from app.reporting.weekly_reporter import WeeklyReporter
from app.core.orchestrator import MasterOrchestrator


class TestTradingDeskIntegrity(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_trading_desk.db")
        self.db = DatabaseManager(db_path=self.test_db_path)
        self.journal = TradeJournal(db=self.db)
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.0, kill_switch_dd_pct=10.0, max_daily_loss_pct=3.0)
        self.desk = DecisionDesk(risk_manager=self.risk, journal=self.journal, confidence_threshold=70.0)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. DATABASE & JOURNAL DELIVERABLES
    # -------------------------------------------------------------
    def test_database_candles_and_backup(self):
        sample_candles = [
            {"time": 1700000000 + (i * 900), "open": 2740.0 + i, "high": 2745.0 + i, "low": 2738.0 + i, "close": 2744.0 + i, "tick_volume": 150 + i, "spread": 25}
            for i in range(50)
        ]
        stored = self.db.store_candles("XAUUSDm", "M15", sample_candles)
        self.assertEqual(stored, 50)

        df = self.db.get_candles_df("XAUUSDm", "M15", limit=30)
        self.assertEqual(len(df), 30)
        self.assertIn("close", df.columns)

        # Automated Backup Test
        backup_file = self.db.backup_database()
        self.assertTrue(os.path.exists(backup_file))

        # CSV Export Test
        exports = self.db.export_journal_csv(output_dir=os.path.join(self.test_dir, "exports"))
        self.assertTrue(os.path.exists(exports["decisions_csv"]))
        self.assertTrue(os.path.exists(exports["trades_csv"]))

    def test_journal_pre_trade_and_post_trade_logging(self):
        # 1. Log pre-trade decision
        dec_id = self.journal.log_decision_event(
            symbol="XAUUSDm",
            timeframe="M15",
            consensus_bias="BUY",
            confidence=85.0,
            agreement_count=4,
            trigger_reason="Asian Range Liquidity Sweep + Bullish EMA Stack",
            entry_price=2750.0,
            stop_loss=2747.5,
            take_profit=2756.25,
            agent_votes={"trend": "BUY", "liquidity": "BUY"},
            features_snapshot={"rsi_14": 58.2},
            risk_status="APPROVED",
            executed=True
        )
        self.assertGreater(dec_id, 0)

        # 2. Log Trade Execution
        self.journal.log_trade_execution(
            ticket=99901,
            decision_id=dec_id,
            symbol="XAUUSDm",
            side="BUY",
            volume=0.01,
            entry_price=2750.0,
            stop_loss=2747.5,
            take_profit=2756.25,
            slippage=0.10
        )

        # 3. Log Trade Closure with Profit & Realized R
        self.journal.log_trade_outcome(
            ticket=99901,
            close_price=2756.25,
            profit=6.25,
            status="CLOSED_TP",
            close_reason="Target Hit"
        )

        # 4. Verify Edge Analysis
        edge = self.journal.analyze_statistical_edge()
        self.assertEqual(edge["total_trades"], 1)
        self.assertEqual(edge["win_rate"], 100.0)
        self.assertEqual(edge["avg_r"], 2.5)

    # -------------------------------------------------------------
    # 2. SOVEREIGN RISK MANAGER DELIVERABLE
    # -------------------------------------------------------------
    def test_risk_manager_mandatory_stop_loss(self):
        # Trade without SL must be REJECTED unconditionally
        plan = self.risk.evaluate_and_size_trade(
            account_balance=100.0,
            side="BUY",
            entry_price=2750.0,
            stop_loss=0.0,  # Missing SL
            take_profit=2760.0,
            symbol="XAUUSDm"
        )
        self.assertIsNone(plan, "Trades without stop loss must be rejected")

    def test_risk_manager_emergency_kill_switch(self):
        self.risk.peak_equity = 100.0
        # 5% drawdown -> OK
        res1 = self.risk.evaluate_kill_switch(95.0)
        self.assertFalse(res1["kill_switch"])

        # 10.5% drawdown -> TRIGGER KILL SWITCH
        res2 = self.risk.evaluate_kill_switch(89.5)
        self.assertTrue(res2["kill_switch"])
        self.assertEqual(res2["action"], "close_all_and_halt")

    def test_risk_manager_daily_loss_limit(self):
        self.risk.update_account_state(100.0, 100.0)
        self.risk.daily_pnl = -3.50  # 3.5% loss on 100.0
        is_allowed = self.risk.evaluate_daily_loss_limit(96.5)
        self.assertFalse(is_allowed, "Breaching 3% daily loss must halt trading")

    # -------------------------------------------------------------
    # 3. SPECIALIST AGENTS & DECISION DESK DELIVERABLE
    # -------------------------------------------------------------
    def test_specialist_agents_and_decision_desk_consensus(self):
        # Create synthetic bullish candle series
        prices = [2740.0 + (i * 0.5) for i in range(50)]
        df_bull = pd.DataFrame({
            "open": [p - 0.2 for p in prices],
            "high": [p + 0.6 for p in prices],
            "low": [p - 0.4 for p in prices],
            "close": prices,
            "tick_volume": [200] * 50
        })

        market_metrics = {
            "spread": 0.25,
            "session": "LONDON",
            "is_killzone": True,
            "atr_14": 1.5,
            "rsi_14": 62.0,
            "ema_20": 2760.0
        }

        # Decision Desk evaluation
        ticket = self.desk.evaluate_symbol(
            symbol="XAUUSDm",
            df_m15=df_bull,
            market_metrics=market_metrics,
            account_equity=100.0
        )
        self.assertTrue(ticket.get("approved"))
        self.assertEqual(ticket["side"], "BUY")
        self.assertGreaterEqual(ticket["agreement_count"], 3)
        self.assertGreaterEqual(ticket["confidence"], 70.0)
        self.assertGreaterEqual(ticket["risk_reward_ratio"], 2.0)

    # -------------------------------------------------------------
    # 4. BACKTESTER & WALK-FORWARD TESTING DELIVERABLE
    # -------------------------------------------------------------
    def test_walk_forward_backtester(self):
        # Generate 200 synthetic candles
        np.random.seed(42)
        steps = np.random.normal(loc=0.05, scale=0.8, size=200)
        walk = 2700.0 + np.cumsum(steps)

        df_candles = pd.DataFrame({
            "open": walk - 0.2,
            "high": walk + 1.2,
            "low": walk - 1.2,
            "close": walk,
            "tick_volume": [200] * 200
        })

        bt = WalkForwardBacktester(initial_capital=100.0, risk_percent=1.0)
        res = bt.walk_forward_validation(df_candles, split_ratio=0.70)

        self.assertIn("in_sample", res)
        self.assertIn("out_of_sample", res)
        self.assertIn("walk_forward_efficiency_pct", res)
        self.assertGreater(res["in_sample"]["period_bars"], 100)
        self.assertGreater(res["out_of_sample"]["period_bars"], 50)

    # -------------------------------------------------------------
    # 5. WEEKLY AUDIT REPORTER DELIVERABLE
    # -------------------------------------------------------------
    def test_weekly_reporter_markdown_generation(self):
        reporter = WeeklyReporter(journal=self.journal)
        md = reporter.generate_report_markdown()
        self.assertIn("Weekly Institutional Trading Desk Performance Audit", md)
        self.assertIn("Executive Summary", md)
        self.assertIn("Statistical Edge & Sample Size Audit", md)

    # -------------------------------------------------------------
    # 6. ORCHESTRATOR & 10 ROBOTS WORKFORCE 2.0
    # -------------------------------------------------------------
    def test_orchestrator_workforce_2_0(self):
        orch = MasterOrchestrator()
        self.assertEqual(len(orch.agents), 10, "Workforce 2.0 must have 10 specialized robot employees")
        agent_names = [a["name"] for a in orch.agents]
        self.assertIn("Zara", agent_names)
        self.assertIn("Kai", agent_names)
        self.assertIn("Aria", agent_names)

        # Telegram Desk & Edge commands
        desk_reply = orch.handle_telegram_command("/desk")
        self.assertIn("Decision Desk", desk_reply)

        edge_reply = orch.handle_telegram_command("/edge")
        self.assertIn("Statistical Edge Audit", edge_reply)


if __name__ == "__main__":
    unittest.main()
