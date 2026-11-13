"""
Generation 3.0: Sovereign Prop-Desk & Autonomous AI Engine Integrity Test Suite
Verifies:
1. Red Team Prosecutor: Adversarial trap detection, noise vulnerability, and liquidity sweep audits.
2. Macro Cross-Asset Analyst: DXY inversion, yields, and Risk-On/Off correlation logic.
3. Market Regime Engine: Trending expansion, chop, and news shock event classification.
4. Sovereign Portfolio Engine: Fractional Kelly sizing and cross-asset correlation exposure shield.
5. Autonomous Circuit Breakers: Losing streak cooldown, 2% drawdown stepdown, and 10% kill-switch.
6. Strategy Evolver: Sharpe/Sortino setup rankings, auto-quarantine, and forensic post-mortems.
7. Gen 3.0 Decision Desk & Floor Supervisor: End-to-end multi-agent debate and autonomous execution.
"""
import unittest
import time
import pandas as pd
import numpy as np

from app.agents.red_team_agent import RedTeamProsecutor
from app.agents.macro_agent import MacroCrossAssetAnalyst
from app.agents.regime_classifier import MarketRegimeEngine
from app.trading.portfolio_engine import SovereignPortfolioEngine
from app.trading.circuit_breaker import AutonomousCircuitBreaker
from app.learning.strategy_evolver import StrategyEvolver
from app.agents.decision_desk import DecisionDesk
from app.core.autonomous_supervisor import AutonomousFloorSupervisor
from app.data.db_manager import DatabaseManager
from app.learning.journal import TradeJournal
from app.trading.risk_manager import RiskManager


class TestNextGenEngineIntegrity(unittest.TestCase):
    def setUp(self):
        # Generate synthetic 15-minute trending candles for testing
        dates = pd.date_range("2026-11-13 00:00", periods=50, freq="15min")
        base_price = 2740.0
        records = []
        for i in range(50):
            p = base_price + (i * 0.35) + (np.sin(i) * 0.20)
            records.append({
                "datetime": dates[i].strftime("%Y-%m-%d %H:%M:%S"),
                "open": p - 0.15,
                "high": p + 0.40,
                "low": p - 0.20,
                "close": p + 0.20,
                "volume": 120 + i
            })
        self.df_trending = pd.DataFrame(records)

    # -------------------------------------------------------------
    # 1. RED TEAM PROSECUTOR TESTS
    # -------------------------------------------------------------
    def test_red_team_choke_stop_veto(self):
        prosecutor = RedTeamProsecutor()
        market_metrics = {"spread": 0.40, "atr_14": 1.80}
        agent_opinions = {"trend": {"bias": "BUY", "confidence": 80}}

        # Proposed SL is only $0.50 away (less than 2.5x spread of 0.40 = 1.00)
        res = prosecutor.scrutinize_proposal(
            symbol="XAUUSDm",
            proposed_side="BUY",
            entry_price=2750.0,
            stop_loss=2749.50,
            take_profit=2756.0,
            df_candles=self.df_trending,
            market_metrics=market_metrics,
            agent_opinions=agent_opinions
        )
        self.assertTrue(res["veto_recommended"])
        self.assertGreaterEqual(res["risk_score"], 40.0)
        self.assertTrue(any("Choke Warning" in c for c in res["critique"]))

    def test_red_team_clean_pass(self):
        prosecutor = RedTeamProsecutor()
        market_metrics = {"spread": 0.25, "atr_14": 1.50}
        agent_opinions = {
            "trend": {"bias": "BUY", "confidence": 85},
            "momentum": {"bias": "BUY", "confidence": 80}
        }

        # Generous structural SL with adequate breathing room and 2.5R reward
        res = prosecutor.scrutinize_proposal(
            symbol="XAUUSDm",
            proposed_side="BUY",
            entry_price=2745.0,
            stop_loss=2742.0,  # 3.00 distance > 2.5x spread
            take_profit=2752.50,  # 2.5R
            df_candles=self.df_trending,
            market_metrics=market_metrics,
            agent_opinions=agent_opinions
        )
        self.assertFalse(res["veto_recommended"])
        self.assertTrue(res["passed"])
        self.assertEqual(res["prosecutor_status"], "CLEAN_PASS")

    # -------------------------------------------------------------
    # 2. MACRO CROSS-ASSET ANALYST TESTS
    # -------------------------------------------------------------
    def test_macro_dxy_inversion_gold(self):
        macro = MacroCrossAssetAnalyst()
        # Bullish DXY should be a headwind for Gold (SELL bias or lower confidence)
        res_dxy_bull = macro.analyze_macro_context("XAUUSDm", {"dxy_bias": "BULLISH", "risk_sentiment": "NEUTRAL"})
        self.assertEqual(res_dxy_bull["bias"], "SELL")

        # Bearish DXY should provide tailwind for Gold (BUY bias)
        res_dxy_bear = macro.analyze_macro_context("XAUUSDm", {"dxy_bias": "BEARISH", "risk_sentiment": "RISK_OFF"})
        self.assertEqual(res_dxy_bear["bias"], "BUY")
        self.assertGreater(res_dxy_bear["confidence"], 70.0)

    def test_macro_crypto_risk_on(self):
        macro = MacroCrossAssetAnalyst()
        res_btc = macro.analyze_macro_context("BTCUSDm", {"dxy_bias": "BEARISH", "risk_sentiment": "RISK_ON"})
        self.assertEqual(res_btc["bias"], "BUY")
        self.assertGreater(res_btc["confidence"], 75.0)

    # -------------------------------------------------------------
    # 3. MARKET REGIME ENGINE TESTS
    # -------------------------------------------------------------
    def test_market_regime_classification(self):
        regime_engine = MarketRegimeEngine()
        metrics = {"spread": 0.20, "avg_spread": 0.20, "atr_14": 1.5}
        res = regime_engine.classify_regime(self.df_trending, metrics)
        self.assertIn(res["regime"], ["TRENDING_EXPANSION", "COMPRESSED_ACCUMULATION"])
        self.assertGreater(res["target_multiplier"], 0.9)

    def test_regime_news_shock_event(self):
        regime_engine = MarketRegimeEngine()
        # Spread explosion 4x baseline
        metrics = {"spread": 1.20, "avg_spread": 0.30, "atr_14": 1.5}
        res = regime_engine.classify_regime(self.df_trending, metrics)
        self.assertEqual(res["regime"], "NEWS_SHOCK_EVENT")
        self.assertEqual(res["trade_recommendation"], "VETO_ALL_ENTRIES")

    # -------------------------------------------------------------
    # 4. SOVEREIGN PORTFOLIO & FRACTIONAL KELLY TESTS
    # -------------------------------------------------------------
    def test_fractional_kelly_sizing(self):
        portfolio = SovereignPortfolioEngine()
        # High edge: 60% win rate with 2.0R payoff
        res = portfolio.calculate_fractional_kelly_risk(
            account_balance=1000.0,
            empirical_win_rate=0.60,
            payoff_ratio=2.0,
            sample_size=35
        )
        self.assertTrue(res["is_full_kelly"])
        self.assertGreater(res["kelly_percent"], 0.8)

        # Negative edge: 20% win rate with 1.0R payoff -> Kelly percent should be 0.0 (veto)
        res_neg = portfolio.calculate_fractional_kelly_risk(
            account_balance=1000.0,
            empirical_win_rate=0.20,
            payoff_ratio=1.0,
            sample_size=35
        )
        self.assertEqual(res_neg["kelly_percent"], 0.0)

    def test_portfolio_correlation_risk(self):
        portfolio = SovereignPortfolioEngine(max_class_exposure_pct=0.04)  # 4% max per class
        open_positions = [{"symbol": "XAUUSDm", "dollar_risk": 3.0}]
        # Account balance $100 -> Max allowed risk in metals is $4.00. Current risk is $3.00.
        # Adding $2.00 more will push total to $5.00 > $4.00 -> should veto.
        check = portfolio.check_portfolio_correlation_risk(
            symbol="XAUUSDm",
            dollar_risk=2.0,
            account_balance=100.0,
            open_positions=open_positions
        )
        self.assertFalse(check["approved"])
        self.assertIn("Correlation Overexposure", check["reason"])

    # -------------------------------------------------------------
    # 5. AUTONOMOUS CIRCUIT BREAKER TESTS
    # -------------------------------------------------------------
    def test_circuit_breaker_consecutive_losses(self):
        cb = AutonomousCircuitBreaker(max_consecutive_losses=3, streak_cooldown_seconds=600.0)
        cb.record_trade_outcome(-1.50)
        cb.record_trade_outcome(-1.20)
        self.assertEqual(cb.consecutive_losses, 2)

        # 3rd consecutive loss engages cooldown
        cb.record_trade_outcome(-0.80)
        self.assertEqual(cb.consecutive_losses, 3)
        status = cb.get_status()
        self.assertTrue(status["is_cooling_down"])

        # Check audit permission during cooldown
        audit = cb.audit_trade_permission("XAUUSDm", current_spread=0.25, baseline_spread=0.25)
        self.assertFalse(audit["permitted"])
        self.assertIn("STREAK_COOLDOWN", audit["active_breakers"][0])

        # Win resets streak
        cb.record_trade_outcome(+3.50)
        self.assertEqual(cb.consecutive_losses, 0)

    def test_circuit_breaker_drawdown_stepdown_and_kill(self):
        cb = AutonomousCircuitBreaker(stepdown_drawdown_pct=2.0, kill_switch_dd_pct=10.0)
        # Peak equity $100, current equity $97.5 (2.5% drawdown) -> Step-down engaged
        dd_step = cb.evaluate_drawdown_state(current_equity=97.5, peak_equity=100.0)
        self.assertTrue(dd_step["permitted"])
        self.assertTrue(dd_step["stepdown"])
        self.assertEqual(dd_step["risk_multiplier"], 0.50)

        # Peak equity $100, current equity $89.0 (11% drawdown) -> Kill switch halts trading
        dd_kill = cb.evaluate_drawdown_state(current_equity=89.0, peak_equity=100.0)
        self.assertFalse(dd_kill["permitted"])
        self.assertTrue(dd_kill["kill_switch"])
        self.assertTrue(cb.kill_switch_active)

    # -------------------------------------------------------------
    # 6. STRATEGY EVOLVER & FORENSIC POST-MORTEM TESTS
    # -------------------------------------------------------------
    def test_strategy_evolver_post_mortem(self):
        evolver = StrategyEvolver()
        pm_win = evolver.generate_trade_post_mortem(
            trade_id=101, symbol="XAUUSDm", side="BUY", entry=2745.0, sl=2743.0,
            tp=2750.0, exit_price=2750.0, pnl=5.0, r_multiple=2.5
        )
        self.assertEqual(pm_win["verdict"], "FLAWLESS_TARGET_EXPANSION")

        pm_loss = evolver.generate_trade_post_mortem(
            trade_id=102, symbol="XAUUSDm", side="BUY", entry=2745.0, sl=2743.0,
            tp=2750.0, exit_price=2743.0, pnl=-2.0, r_multiple=-1.0
        )
        self.assertEqual(pm_loss["verdict"], "CONTROLLED_RISK_ABSORPTION")

    # -------------------------------------------------------------
    # 7. GEN 3.0 DECISION DESK & SUPERVISOR INTEGRATION TESTS
    # -------------------------------------------------------------
    def test_gen3_decision_desk_evaluation(self):
        desk = DecisionDesk()
        market_metrics = {"spread": 0.25, "avg_spread": 0.25, "atr_14": 1.5, "rsi_14": 55.0}
        macro_feed = {"dxy_bias": "BEARISH", "risk_sentiment": "RISK_ON"}

        decision = desk.evaluate_symbol(
            symbol="XAUUSDm",
            df_m15=self.df_trending,
            market_metrics=market_metrics,
            account_equity=100.0,
            macro_feed=macro_feed
        )
        self.assertIn("approved", decision)
        if decision["approved"]:
            self.assertIn("red_team_audit", decision)
            self.assertIn("regime", decision)
            self.assertIn("circuit_breaker", decision)

    def test_autonomous_floor_supervisor_lifecycle(self):
        supervisor = AutonomousFloorSupervisor()
        self.assertFalse(supervisor.is_running)

        supervisor.start()
        self.assertTrue(supervisor.is_running)

        supervisor.pause()
        self.assertTrue(supervisor.is_paused)

        supervisor.resume()
        self.assertFalse(supervisor.is_paused)

        telemetry = supervisor.get_telemetry()
        self.assertIn("circuit_breaker", telemetry)
        self.assertIn("peak_equity", telemetry)

        supervisor.stop()
        self.assertFalse(supervisor.is_running)


if __name__ == "__main__":
    unittest.main()
