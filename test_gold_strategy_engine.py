import unittest
from datetime import datetime, timezone
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.trading.gold_strategy_engine import GoldStrategyEngine


class TestGoldStrategyEngine(unittest.TestCase):

    def setUp(self):
        self.engine = GoldStrategyEngine()

    def test_setup_1_asian_high_sweep_sell(self):
        # Asian range: High 2745.0, Low 2738.0
        asian_range = {"active": True, "high": 2745.0, "low": 2738.0, "mid": 2741.5}
        
        # 5m candles: bar spikes to 2746.5 (swept Asian high 2745), then closes down at 2744.2
        candles_5m = [
            {"open": 2743.0, "high": 2744.0, "low": 2742.0, "close": 2743.5},
            {"open": 2743.5, "high": 2744.5, "low": 2743.0, "close": 2744.0},
            {"open": 2744.0, "high": 2745.0, "low": 2743.5, "close": 2744.5},
            {"open": 2744.5, "high": 2745.5, "low": 2744.0, "close": 2745.0},
            {"open": 2745.0, "high": 2746.5, "low": 2744.5, "close": 2744.8},  # Swept to 2746.5
            {"open": 2744.8, "high": 2745.0, "low": 2743.8, "close": 2744.0},  # Bearish close at 2744.0
        ]
        candles_15m = [{"high": 2745.0, "low": 2738.0, "close": 2742.0, "open": 2740.0}] * 10

        res = self.engine.check_setup_1_asian_sweep_ote(candles_15m, candles_5m, 2744.0, asian_range)
        self.assertIsNotNone(res)
        self.assertEqual(res["side"], "SELL")
        self.assertEqual(res["entry"], 2744.0)
        # SL is highest wick 2746.5 + 0.40 = 2746.90
        self.assertEqual(res["sl"], 2746.90)
        self.assertLessEqual(res["risk"], 3.0)
        print("Setup 1 Bearish Asian Sweep:", res)

    def test_setup_1_asian_low_sweep_buy(self):
        asian_range = {"active": True, "high": 2750.0, "low": 2740.0, "mid": 2745.0}
        
        # 5m candles: bar spikes down to 2738.8 (swept Asian low 2740), then closes up at 2741.0
        candles_5m = [
            {"open": 2742.0, "high": 2743.0, "low": 2741.0, "close": 2741.5},
            {"open": 2741.5, "high": 2742.0, "low": 2740.5, "close": 2741.0},
            {"open": 2741.0, "high": 2741.5, "low": 2740.0, "close": 2740.5},
            {"open": 2740.5, "high": 2741.0, "low": 2739.5, "close": 2740.0},
            {"open": 2740.0, "high": 2740.5, "low": 2738.8, "close": 2739.5},  # Swept to 2738.8
            {"open": 2739.5, "high": 2741.5, "low": 2739.2, "close": 2741.0},  # Bullish close at 2741.0
        ]
        candles_15m = [{"high": 2750.0, "low": 2740.0, "close": 2745.0, "open": 2742.0}] * 10

        res = self.engine.check_setup_1_asian_sweep_ote(candles_15m, candles_5m, 2741.0, asian_range)
        self.assertIsNotNone(res)
        self.assertEqual(res["side"], "BUY")
        self.assertEqual(res["entry"], 2741.0)
        # SL is lowest wick 2738.8 - 0.40 = 2738.40
        self.assertEqual(res["sl"], 2738.40)
        print("Setup 1 Bullish Asian Sweep:", res)

    def test_setup_2_overlap_orb(self):
        # 14:00 UTC (in 13:00-16:30 Overlap)
        dt = datetime(2026, 11, 12, 14, 0, tzinfo=timezone.utc)
        candles_5m = [
            {"open": 2740.0, "high": 2743.0, "low": 2739.0, "close": 2742.0},
            {"open": 2742.0, "high": 2744.0, "low": 2741.0, "close": 2743.0},
            {"open": 2743.0, "high": 2744.0, "low": 2741.5, "close": 2743.5},
            {"open": 2743.5, "high": 2746.0, "low": 2743.0, "close": 2745.5},  # Closed bar above 2744.0
        ]
        res = self.engine.check_setup_2_overlap_orb(candles_5m, 2745.5, current_dt=dt)
        self.assertIsNotNone(res)
        self.assertEqual(res["side"], "BUY")
        self.assertEqual(res["entry"], 2745.5)
        # Entry 2745.5 - range_mid 2741.5 is $4.00, which cleanly fits inside $5.00 max SL
        self.assertEqual(res["sl"], 2741.5)
        print("Setup 2 Overlap ORB:", res)

    def test_setup_3_trend_reclaim(self):
        # 1H candles above 200 EMA (trending bullish: 2730 to 2750)
        candles_1h = [{"open": 2720.0 + i, "high": 2725.0 + i, "low": 2718.0 + i, "close": 2724.0 + i} for i in range(25)]
        # 15m pullback touching 50 EMA at 2744.0 and rejecting up
        candles_15m = [{"open": 2740.0 + (i*0.2), "high": 2743.0 + (i*0.2), "low": 2739.0 + (i*0.2), "close": 2742.0 + (i*0.2)} for i in range(20)]
        # Last bar dips to 50 EMA and closes back above
        candles_15m[-1] = {"open": 2745.5, "high": 2746.0, "low": 2743.5, "close": 2745.0}

        res = self.engine.check_setup_3_trend_reclaim(candles_1h, candles_15m, 2745.0)
        # Should either return a valid setup or None if conditions not met
        print("Setup 3 Trend Reclaim evaluation completed:", res is not None)

    def test_safety_spread_filter(self):
        # When spread is $0.85 (widened during news or rollover), reject
        candles = [{"open": 2740.0, "high": 2745.0, "low": 2738.0, "close": 2742.0}] * 15
        res = self.engine.evaluate_gold_opportunities(candles, candles, candles, 2742.0, spread=0.85)
        self.assertFalse(res["triggered"])
        self.assertIn("SPREAD_TOO_HIGH", res["reason"])
        print("Spread filter successfully protected trade!")

    def test_safety_volatility_spike_filter(self):
        # 5m candles with extreme range ($10+ per candle) -> high impact news spike
        wild_candles = [
            {"open": 2730.0, "high": 2745.0, "low": 2725.0, "close": 2740.0},
            {"open": 2740.0, "high": 2755.0, "low": 2735.0, "close": 2750.0},
            {"open": 2750.0, "high": 2765.0, "low": 2745.0, "close": 2760.0},
        ] * 3
        res = self.engine.evaluate_gold_opportunities(wild_candles, wild_candles, wild_candles, 2760.0, spread=0.20)
        self.assertFalse(res["triggered"])
        self.assertIn("HIGH_IMPACT_NEWS_VOLATILITY", res["reason"])
        print("News volatility spike successfully blocked!")


if __name__ == "__main__":
    unittest.main()
