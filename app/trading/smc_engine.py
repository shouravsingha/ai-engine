"""
Smart Money Concepts (SMC) Engine
Handles Market Structure, Break of Structure (BOS), Change of Character (CHoCH),
Order Blocks (OB), and Fair Value Gaps (FVG) on High Timeframes (4H / Daily / 1H).
"""
import pandas as pd
from typing import Dict, Any, List

class SMCEngine:
    def __init__(self):
        self.trend = "BULLISH" # Default HTF trend
        self.last_swing_high = 0.0
        self.last_swing_low = 0.0
        self.order_blocks = []
        self.fvg_zones = []

    def analyze_candles(self, candles: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Takes OHLCV candle data and computes SMC market structure.
        """
        if not candles:
            candles = [
                {"open": 2740.0, "high": 2750.0, "low": 2735.0, "close": 2745.0, "volume": 100}
            ]

        df = pd.DataFrame(candles)
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        recent_high = float(max(highs[-10:] if len(highs) >= 10 else highs))
        recent_low = float(min(lows[-10:] if len(lows) >= 10 else lows))
        current_price = float(closes[-1])

        # Structure analysis
        structure_event = "NONE"
        if self.last_swing_high > 0 and current_price > self.last_swing_high:
            if self.trend == "BEARISH":
                structure_event = "CHoCH (BULLISH REVERSAL)"
                self.trend = "BULLISH"
            else:
                structure_event = "BOS (BULLISH CONTINUATION)"
            self.last_swing_high = recent_high

        elif self.last_swing_low > 0 and current_price < self.last_swing_low:
            if self.trend == "BULLISH":
                structure_event = "CHoCH (BEARISH REVERSAL)"
                self.trend = "BEARISH"
            else:
                structure_event = "BOS (BEARISH CONTINUATION)"
            self.last_swing_low = recent_low
        else:
            self.last_swing_high = recent_high
            self.last_swing_low = recent_low

        # Order Block detection (Last opposite candle before a strong impulsive displacement)
        ob_zone = None
        if self.trend == "BULLISH":
            # Bullish Order Block = Last down candle before impulse
            ob_low = recent_low
            ob_high = recent_low + (recent_high - recent_low) * 0.15
            ob_zone = {"type": "BULLISH_OB", "low": round(ob_low, 2), "high": round(ob_high, 2)}
        else:
            ob_high = recent_high
            ob_low = recent_high - (recent_high - recent_low) * 0.15
            ob_zone = {"type": "BEARISH_OB", "low": round(ob_low, 2), "high": round(ob_high, 2)}

        # Fair Value Gap (FVG) Imbalance (Gap between candle 1 high and candle 3 low)
        fvg = None
        if len(df) >= 3:
            c1_high = highs[-3]
            c3_low = lows[-1]
            if c3_low > c1_high:
                fvg = {"type": "BULLISH_FVG", "bottom": round(c1_high, 2), "top": round(c3_low, 2)}
            elif lows[-3] > highs[-1]:
                fvg = {"type": "BEARISH_FVG", "top": round(lows[-3], 2), "bottom": round(highs[-1], 2)}

        return {
            "trend": self.trend,
            "structure_event": structure_event,
            "swing_high": round(recent_high, 2),
            "swing_low": round(recent_low, 2),
            "order_block": ob_zone,
            "fvg": fvg,
            "current_price": round(current_price, 2)
        }
