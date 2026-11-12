"""
Comprehensive System Integrity & Regression Test Suite for ai-engine
Tests:
1. Risk Manager & Contract Sizes
2. Time Machine Monte Carlo Engine
3. Session ORB & Closed-Bar Breakout Engine
4. AI Central Neural Brain Discipline & Circuit Breakers
5. Master Orchestrator End-to-End Execution Flow
6. Exness Bridge Safety Locks
7. FastAPI Telemetry & Endpoints
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.trading.risk_manager import RiskManager
from app.trading.time_machine import TimeMachineEngine
from app.trading.orb_engine import SessionORBEngine
from app.core.ai_brain import AIBrainOverseer
from app.core.orchestrator import MasterOrchestrator
from app.trading.exness_bridge import ExnessBridge
from main import app


class TestSystemIntegrity(unittest.TestCase):

    def setUp(self):
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.5)
        self.time_machine = TimeMachineEngine(default_replays=1000, horizon_bars=20, seed=42)
        self.orb = SessionORBEngine(or_minutes=15, default_target_r=2.5)
        self.brain = AIBrainOverseer()

    # -------------------------------------------------------------
    # 1. RISK MANAGER TESTS
    # -------------------------------------------------------------
    def test_risk_contract_sizes(self):
        self.assertEqual(self.risk.get_contract_size("XAUUSDm"), 100.0)
        self.assertEqual(self.risk.get_contract_size("BTCUSDm"), 1.0)
        self.assertEqual(self.risk.get_contract_size("ETHUSDm"), 1.0)
        self.assertEqual(self.risk.get_contract_size("EURUSDm"), 100000.0)

    def test_risk_micro_account_protection(self):
        # On $20 balance, micro tier applies
        bal = 20.0
        tier = self.risk.get_capital_tier(bal)
        self.assertEqual(tier["tier"], "MICRO")
        self.assertEqual(tier["max_positions"], 1)
        self.assertEqual(tier["volume_cap"], 0.01)

        # Huge SL on Gold ($10 distance with 0.01 lot = $10 loss = 50% of account) MUST be rejected!
        plan = self.risk.evaluate_and_size_trade(bal, "BUY", entry=2750.0, sl=2740.0, tp=2775.0, symbol="XAUUSDm")
        self.assertIsNone(plan, "Risk manager must reject trade whose min lot loss exceeds risk ceiling")

        # Small safe SL on Gold ($0.80 distance with 0.01 lot = $0.80 loss = 4% of account) should be allowed
        safe_plan = self.risk.evaluate_and_size_trade(bal, "BUY", entry=2750.0, sl=2749.20, tp=2753.0, symbol="XAUUSDm")
        self.assertIsNotNone(safe_plan)
        self.assertEqual(safe_plan["volume"], 0.01)
        self.assertLessEqual(safe_plan["dollar_risk"], 1.25)

    def test_risk_depleted_capital_lock(self):
        # Balance under $5.00 must return None
        plan = self.risk.evaluate_and_size_trade(4.50, "BUY", 2750.0, 2749.0, 2753.0, symbol="XAUUSDm")
        self.assertIsNone(plan)

    # -------------------------------------------------------------
    # 2. TIME MACHINE ENGINE TESTS
    # -------------------------------------------------------------
    def test_time_machine_simulation(self):
        res = self.time_machine.simulate_trade("XAUUSDm", "BUY", entry=2750.0, sl=2748.0, tp=2755.0)
        self.assertTrue(res["prob_target_pct"] >= 0)
        self.assertTrue(res["prob_stop_pct"] >= 0)
        self.assertIn(res["verdict"], [
            "STRONG_TARGET_EDGE", "LEANS_TARGET", "COIN_FLIP_NEUTRAL", "LEANS_STOP", "STRONG_STOP_BIAS"
        ])

    def test_time_machine_invalid_geometry(self):
        # SL above entry for BUY
        res = self.time_machine.simulate_trade("XAUUSDm", "BUY", 2750.0, 2755.0, 2760.0)
        self.assertFalse(res["approved"])

    # -------------------------------------------------------------
    # 3. SESSION ORB TESTS
    # -------------------------------------------------------------
    def test_session_orb_breakout_and_wick(self):
        candles_valid = [
            {"open": 2740.0, "high": 2743.0, "low": 2739.0, "close": 2742.0},
            {"open": 2742.0, "high": 2744.0, "low": 2740.0, "close": 2743.0},
            {"open": 2743.0, "high": 2744.0, "low": 2741.0, "close": 2742.5},
            {"open": 2742.5, "high": 2746.0, "low": 2742.0, "close": 2745.5},  # Closed above 2744.0
        ]
        res = self.orb.analyze_orb_breakout("XAUUSDm", 2745.5, candles_valid)
        self.assertEqual(res["status"], "TRIGGERED")
        self.assertEqual(res["setup"]["side"], "BUY")

        # Wick test: Candle high is 2747, but close is 2742 (inside range)
        candles_wick = [
            {"open": 2740.0, "high": 2743.0, "low": 2739.0, "close": 2742.0},
            {"open": 2742.0, "high": 2744.0, "low": 2740.0, "close": 2743.0},
            {"open": 2743.0, "high": 2744.0, "low": 2741.0, "close": 2742.5},
            {"open": 2742.5, "high": 2747.0, "low": 2741.0, "close": 2742.0},
        ]
        res_wick = self.orb.analyze_orb_breakout("XAUUSDm", 2742.0, candles_wick)
        self.assertEqual(res_wick["status"], "INSIDE_RANGE")
        self.assertIsNone(res_wick["setup"])

    # -------------------------------------------------------------
    # 4. AI BRAIN TESTS
    # -------------------------------------------------------------
    def test_brain_emergency_circuit_breaker(self):
        # Open position with floating loss of -$1.35
        mock_positions = [{
            "ticket": 1001,
            "symbol": "XAUUSDm",
            "side": "BUY",
            "open_price": 2750.0,
            "current_price": 2748.65,
            "sl": 2745.0,
            "tp": 2760.0,
            "profit": -1.35
        }]
        actions = self.brain.evaluate_open_positions(mock_positions, {})
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action"], "close_position")
        self.assertIn("EMERGENCY CIRCUIT BREAKER", actions[0]["reason"])

    def test_brain_time_machine_veto(self):
        tm_negative = {
            "approved": False,
            "verdict": "STRONG_STOP_BIAS",
            "resolved_winrate_pct": 20.0,
            "breakeven_winrate_pct": 50.0,
            "expected_r": -0.35
        }
        audit = self.brain.audit_trade_proposal("TestAgent", "XAUUSDm", "BUY", rrr=2.5, risk_pct=1.0, dollar_risk=0.80, balance=20.0, time_machine_audit=tm_negative)
        self.assertFalse(audit["approved"])
        self.assertIn("TIME MACHINE VETO", audit["correction_text"])

    # -------------------------------------------------------------
    # 5. ORCHESTRATOR & TELEGRAM TESTS
    # -------------------------------------------------------------
    def test_orchestrator_initialization_and_scan(self):
        orch = MasterOrchestrator()
        self.assertIsNotNone(orch.time_machine)
        self.assertIsNotNone(orch.orb)
        self.assertIsNotNone(orch.risk)

        # Telegram command processing
        status_res = orch.handle_telegram_command("/status")
        self.assertIn("AI Central Brain", status_res)

        tm_res = orch.handle_telegram_command("/timemachine")
        self.assertIn("Time Machine Monte Carlo", tm_res)

        orb_res = orch.handle_telegram_command("/orb")
        self.assertIn("Session ORB Engine", orb_res)

        # Run scan
        orch.run_simultaneous_scan()
        self.assertIn("gold", orch.multi_market_matrix)
        self.assertIn("orb", orch.multi_market_matrix["gold"])

    # -------------------------------------------------------------
    # 6. FASTAPI ENDPOINTS TEST
    # -------------------------------------------------------------
    def test_fastapi_endpoints_registered(self):
        routes = [r.path for r in app.routes]
        self.assertIn("/api/telemetry", routes)
        self.assertIn("/api/timemachine/simulate", routes)
        self.assertIn("/api/orb/status", routes)


if __name__ == "__main__":
    unittest.main()
