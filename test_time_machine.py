import unittest
from app.trading.time_machine import TimeMachineEngine

class TestTimeMachineEngine(unittest.TestCase):
    def setUp(self):
        self.tm = TimeMachineEngine(default_replays=1000, horizon_bars=30, seed=42)

    def test_buy_simulation_positive_edge(self):
        # Entry 2740, tight SL 2738 ($2 risk), TP 2746 ($6 reward = 3R)
        res = self.tm.simulate_trade("XAUUSDm", "BUY", entry=2740.0, sl=2738.0, tp=2746.0)
        self.assertIn("prob_target_pct", res)
        self.assertIn("prob_stop_pct", res)
        self.assertIn("verdict", res)
        self.assertIn("expected_r", res)
        self.assertEqual(res["target_r"], 3.0)
        print("BUY simulation result:", res["verdict"], "P(TP):", res["prob_target_pct"], "P(SL):", res["prob_stop_pct"], "Exp R:", res["expected_r"])

    def test_sell_simulation(self):
        # Entry 65000, SL 65200 ($200 risk), TP 64400 ($600 reward = 3R)
        res = self.tm.simulate_trade("BTCUSDm", "SELL", entry=65000.0, sl=65200.0, tp=64400.0)
        self.assertIn("prob_target_pct", res)
        self.assertIn("verdict", res)
        self.assertEqual(res["target_r"], 3.0)
        print("SELL simulation result:", res["verdict"], "P(TP):", res["prob_target_pct"], "P(SL):", res["prob_stop_pct"], "Exp R:", res["expected_r"])

    def test_invalid_plans_rejected(self):
        # BUY with SL above entry
        res = self.tm.simulate_trade("XAUUSDm", "BUY", entry=2740.0, sl=2750.0, tp=2760.0)
        self.assertFalse(res["approved"])
        self.assertEqual(res["verdict"], "INVALID_BUY_PLAN")

        # SELL with SL below entry
        res = self.tm.simulate_trade("BTCUSDm", "SELL", entry=65000.0, sl=64800.0, tp=64000.0)
        self.assertFalse(res["approved"])
        self.assertEqual(res["verdict"], "INVALID_SELL_PLAN")

    def test_reproducibility(self):
        tm1 = TimeMachineEngine(default_replays=500, horizon_bars=20, seed=123)
        tm2 = TimeMachineEngine(default_replays=500, horizon_bars=20, seed=123)
        res1 = tm1.simulate_trade("XAUUSDm", "BUY", entry=2740.0, sl=2738.0, tp=2745.0)
        res2 = tm2.simulate_trade("XAUUSDm", "BUY", entry=2740.0, sl=2738.0, tp=2745.0)
        self.assertEqual(res1["prob_target_pct"], res2["prob_target_pct"])
        self.assertEqual(res1["prob_stop_pct"], res2["prob_stop_pct"])
        self.assertEqual(res1["expected_r"], res2["expected_r"])

if __name__ == '__main__':
    unittest.main()
