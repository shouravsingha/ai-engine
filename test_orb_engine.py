import unittest
from datetime import datetime, timezone
from app.trading.orb_engine import SessionORBEngine

class TestSessionORBEngine(unittest.TestCase):
    def setUp(self):
        self.orb = SessionORBEngine(or_minutes=15, default_target_r=2.5)

    def test_session_detection(self):
        # 14:00 UTC should be New York (and London/NY Overlap)
        dt_ny = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
        sess = self.orb.get_current_session(dt_ny)
        self.assertTrue(sess["is_active"])
        self.assertIn("Session", sess["name"])
        print("Session at 14:00 UTC:", sess)

    def test_bullish_closed_bar_breakout(self):
        # 3 opening range candles: 2740 to 2745
        candles = [
            {"open": 2741.0, "high": 2744.0, "low": 2740.0, "close": 2743.0},
            {"open": 2743.0, "high": 2745.0, "low": 2741.0, "close": 2744.0},
            {"open": 2744.0, "high": 2745.0, "low": 2742.0, "close": 2743.5},
            # Bar 4: Closed bar above 2745.0 -> Close 2746.5
            {"open": 2743.5, "high": 2747.0, "low": 2743.0, "close": 2746.5},
        ]
        res = self.orb.analyze_orb_breakout("XAUUSDm", 2746.5, candles, target_r=2.0)
        self.assertEqual(res["status"], "TRIGGERED")
        setup = res["setup"]
        self.assertEqual(setup["side"], "BUY")
        self.assertEqual(setup["entry"], 2746.5)
        # Range high 2745, Range low 2740 -> Range mid = 2742.5
        self.assertEqual(setup["sl"], 2742.5)
        self.assertEqual(setup["confirmation"], "CLOSED_BAR_CONFIRMED")
        print("Bullish ORB Triggered:", setup)

    def test_wick_rejection_no_trigger(self):
        # Range: 2740 to 2745. Bar 4 high is 2748.0 (wick above), but close is 2743.0 (closed inside)
        candles = [
            {"open": 2741.0, "high": 2744.0, "low": 2740.0, "close": 2743.0},
            {"open": 2743.0, "high": 2745.0, "low": 2741.0, "close": 2744.0},
            {"open": 2744.0, "high": 2745.0, "low": 2742.0, "close": 2743.5},
            # Bar 4: Wicked to 2748, but CLOSED inside at 2743.0
            {"open": 2743.5, "high": 2748.0, "low": 2742.0, "close": 2743.0},
        ]
        res = self.orb.analyze_orb_breakout("XAUUSDm", 2743.0, candles)
        self.assertEqual(res["status"], "INSIDE_RANGE")
        self.assertIsNone(res["setup"])
        print("Wick rejection correctly prevented false entry!")

    def test_bearish_breakdown(self):
        # Range: 65000 to 65500
        candles = [
            {"open": 65200.0, "high": 65500.0, "low": 65100.0, "close": 65300.0},
            {"open": 65300.0, "high": 65450.0, "low": 65000.0, "close": 65100.0},
            {"open": 65100.0, "high": 65200.0, "low": 65050.0, "close": 65150.0},
            # Bar 4: Closed bar BELOW 65000.0 -> Close 64920.0
            {"open": 65150.0, "high": 65150.0, "low": 64900.0, "close": 64920.0},
        ]
        res = self.orb.analyze_orb_breakout("BTCUSDm", 64920.0, candles, target_r=2.5)
        self.assertEqual(res["status"], "TRIGGERED")
        setup = res["setup"]
        self.assertEqual(setup["side"], "SELL")
        self.assertEqual(setup["entry"], 64920.0)
        # Range mid: (65500 + 65000) / 2 = 65250.0
        self.assertEqual(setup["sl"], 65250.0)
        print("Bearish Breakdown Triggered:", setup)

if __name__ == '__main__':
    unittest.main()
