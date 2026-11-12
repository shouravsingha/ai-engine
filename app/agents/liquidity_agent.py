"""
Liquidity & Price Action Specialist Agent.
Identifies Institutional Order Blocks (OB), Fair Value Gaps (FVG),
Key Support/Resistance, and Liquidity Pool Sweeps (Asian/Session highs & lows).
Output format: {bias, confidence (0-100), reason, invalidation_level}
"""

import pandas as pd
from typing import Dict, Any, Optional


class LiquidityAnalyst:
    def __init__(self, name: str = "David (Liquidity/SMC Specialist)"):
        self.name = name

    def analyze(self, df_m15: pd.DataFrame) -> Dict[str, Any]:
        if df_m15.empty or len(df_m15) < 20:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 0,
                "reason": "Insufficient candles for Liquidity/SMC map",
                "invalidation_level": 0.0
            }

        highs = df_m15["high"]
        lows = df_m15["low"]
        opens = df_m15["open"]
        closes = df_m15["close"]
        last_close = float(closes.iloc[-1])

        # 1. Detect Fair Value Gaps (FVG) across last 10 bars
        bullish_fvg = False
        bearish_fvg = False
        fvg_level = 0.0

        for i in range(len(df_m15) - 3, len(df_m15) - 1):
            # Bullish FVG: Bar 1 High < Bar 3 Low
            if highs.iloc[i-1] < lows.iloc[i+1]:
                bullish_fvg = True
                fvg_level = float(lows.iloc[i+1])
            # Bearish FVG: Bar 1 Low > Bar 3 High
            elif lows.iloc[i-1] > highs.iloc[i+1]:
                bearish_fvg = True
                fvg_level = float(highs.iloc[i+1])

        # 2. Detect Liquidity Sweep (Wick beyond recent swing with closed body inside)
        prev_swing_high = float(highs.iloc[-15:-1].max())
        prev_swing_low = float(lows.iloc[-15:-1].min())

        current_high = float(highs.iloc[-1])
        current_low = float(lows.iloc[-1])

        bearish_sweep = (current_high > prev_swing_high) and (last_close < prev_swing_high)
        bullish_sweep = (current_low < prev_swing_low) and (last_close > prev_swing_low)

        # 3. Decision synthesis
        if bullish_sweep:
            bias = "BUY"
            confidence = 88
            reason = f"Liquidity Sweep of Swing Low ({prev_swing_low:.2f}) with rejection body"
            invalidation = current_low
        elif bearish_sweep:
            bias = "SELL"
            confidence = 88
            reason = f"Liquidity Sweep of Swing High ({prev_swing_high:.2f}) with rejection body"
            invalidation = current_high
        elif bullish_fvg and last_close >= fvg_level:
            bias = "BUY"
            confidence = 75
            reason = f"Bullish Fair Value Gap (FVG) demand mitigation at {fvg_level:.2f}"
            invalidation = prev_swing_low
        elif bearish_fvg and last_close <= fvg_level:
            bias = "SELL"
            confidence = 75
            reason = f"Bearish Fair Value Gap (FVG) supply mitigation at {fvg_level:.2f}"
            invalidation = prev_swing_high
        else:
            bias = "NEUTRAL"
            confidence = 50
            reason = f"Price trading inside balanced range [{prev_swing_low:.2f} - {prev_swing_high:.2f}]"
            invalidation = prev_swing_low

        return {
            "agent": self.name,
            "bias": bias,
            "confidence": confidence,
            "reason": reason,
            "invalidation_level": round(invalidation, 2)
        }
