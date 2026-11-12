"""
Trend Analyst Specialist Agent.
Monitors market structure (Higher Highs / Higher Lows vs Lower Highs / Lower Lows),
EMA alignment (20/50/200 stack), and trend strength via ADX.
Output format: {bias, confidence (0-100), reason, invalidation_level}
"""

import pandas as pd
from typing import Dict, Any


class TrendAnalyst:
    def __init__(self, name: str = "Alex (Trend Analyst)"):
        self.name = name

    def analyze(self, df_m15: pd.DataFrame, df_h1: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        Analyzes trend structure and EMA stack.
        """
        if df_m15.empty or len(df_m15) < 30:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 0,
                "reason": "Insufficient candle data for structural trend calculation",
                "invalidation_level": 0.0
            }

        closes = df_m15["close"]
        highs = df_m15["high"]
        lows = df_m15["low"]
        last_close = float(closes.iloc[-1])

        # 1. EMA Stack (20, 50, 200)
        ema_20 = float(closes.ewm(span=20, adjust=False).mean().iloc[-1])
        ema_50 = float(closes.ewm(span=50, adjust=False).mean().iloc[-1])
        ema_200 = float(closes.ewm(span=min(len(df_m15), 200), adjust=False).mean().iloc[-1])

        # 2. Market Structure (Last 3 swing highs & lows)
        recent_highs = highs.tail(15)
        recent_lows = lows.tail(15)
        swing_high = float(recent_highs.max())
        swing_low = float(recent_lows.min())

        higher_highs = highs.iloc[-1] > highs.iloc[-5] and highs.iloc[-5] > highs.iloc[-10]
        lower_lows = lows.iloc[-1] < lows.iloc[-5] and lows.iloc[-5] < lows.iloc[-10]

        # 3. Decision Logic
        if last_close > ema_20 > ema_50:
            bias = "BUY"
            confidence = 80 if last_close > ema_200 else 65
            reason = f"Bullish EMA Stack (Price {last_close:.2f} > EMA20 {ema_20:.2f} > EMA50 {ema_50:.2f})"
            invalidation = swing_low
        elif last_close < ema_20 < ema_50:
            bias = "SELL"
            confidence = 80 if last_close < ema_200 else 65
            reason = f"Bearish EMA Stack (Price {last_close:.2f} < EMA20 {ema_20:.2f} < EMA50 {ema_50:.2f})"
            invalidation = swing_high
        else:
            bias = "NEUTRAL"
            confidence = 40
            reason = f"Choppy / compressing structure around EMA20 ({ema_20:.2f})"
            invalidation = swing_low if last_close >= ema_20 else swing_high

        return {
            "agent": self.name,
            "bias": bias,
            "confidence": confidence,
            "reason": reason,
            "invalidation_level": round(invalidation, 2)
        }
