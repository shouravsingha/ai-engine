"""
Unit and Regression Tests for Real-Time Macro Sentiment & Yield Pipeline
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.trading.macro_pipeline import MacroPipeline
from app.core.orchestrator import MasterOrchestrator


class TestMacroPipeline(unittest.TestCase):

    def setUp(self):
        self.macro = MacroPipeline(cache_ttl_seconds=10)

    def test_live_macro_snapshot_structure(self):
        snap = self.macro.get_live_macro_snapshot()
        self.assertIn("dxy", snap)
        self.assertIn("us10y", snap)
        self.assertIn("fed_funds", snap)
        self.assertIn("ml_engine", snap)

        # Values should be reasonable bounds
        self.assertGreater(snap["dxy"]["price"], 80.0)
        self.assertLess(snap["dxy"]["price"], 140.0)
        self.assertGreater(snap["us10y"]["yield_pct"], 1.0)
        self.assertLess(snap["us10y"]["yield_pct"], 10.0)

        # ML Engine metrics
        ml = snap["ml_engine"]
        self.assertGreaterEqual(ml["gold_bullish_index"], 0.0)
        self.assertLessEqual(ml["gold_bullish_index"], 100.0)
        self.assertIn(ml["bias"], ["STRONG_BULLISH", "MODERATE_BULLISH", "NEUTRAL", "MODERATE_BEARISH", "STRONG_BEARISH"])

    def test_macro_veto_logic(self):
        # Scenario 1: Extreme Bullish Macro (DXY & US10Y falling hard)
        # Should approve BUY, and veto SELL
        self.macro._cached_state = {
            "timestamp": "2026-11-15 14:00:00",
            "dxy": {"price": 102.0, "pct_change": -0.8},
            "us10y": {"yield_pct": 4.10, "pct_change": -1.2},
            "fed_funds": {"implied_rate": 4.25, "futures_price": 95.75, "sentiment": "CUT_EXPECTED"},
            "ml_engine": {
                "gold_bullish_index": 82.5,
                "raw_pressure": -0.98,
                "bias": "STRONG_BULLISH",
                "badge": "🟢 MACRO TAILWIND"
            }
        }
        self.macro._last_fetch_ts = 9999999999.0

        buy_audit = self.macro.audit_trade_macro_confluence("BUY")
        self.assertTrue(buy_audit["approved"])
        self.assertIn("MACRO CONFLUENCE", buy_audit["confluence_note"])

        sell_audit = self.macro.audit_trade_macro_confluence("SELL")
        self.assertFalse(sell_audit["approved"])
        self.assertIn("MACRO VETO", sell_audit["veto_reason"])

        # Scenario 2: Extreme Bearish Macro (DXY & US10Y surging)
        # Should veto BUY, and approve SELL
        self.macro._cached_state["ml_engine"]["gold_bullish_index"] = 22.0
        self.macro._cached_state["ml_engine"]["bias"] = "STRONG_BEARISH"

        buy_audit_2 = self.macro.audit_trade_macro_confluence("BUY")
        self.assertFalse(buy_audit_2["approved"])
        self.assertIn("MACRO VETO", buy_audit_2["veto_reason"])

        sell_audit_2 = self.macro.audit_trade_macro_confluence("SELL")
        self.assertTrue(sell_audit_2["approved"])
        self.assertIn("MACRO CONFLUENCE", sell_audit_2["confluence_note"])

    def test_orchestrator_integration_macro_data(self):
        orch = MasterOrchestrator()
        orch.run_simultaneous_scan()
        self.assertIn("gold", orch.multi_market_matrix)
        self.assertIn("macro", orch.multi_market_matrix["gold"])
        macro = orch.multi_market_matrix["gold"]["macro"]
        self.assertIn("ml_engine", macro)
        self.assertIsNotNone(macro["ml_engine"]["gold_bullish_index"])


if __name__ == "__main__":
    unittest.main()
