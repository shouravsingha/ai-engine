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
        if len(candles) < 15:
            return {"status": "insufficient_data", "trend": self.trend}

        df = pd.DataFrame(candles)
        
        # Calculate local swing highs and lows
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values

        recent_high = max(highs[-10:])
        recent_low = min(lows[-10:])
        current_price = closes[-1]

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
