"""
Momentum Analyst Specialist Agent.
Calculates RSI momentum, MACD histogram crossovers, and regular divergences.
Output format: {bias, confidence (0-100), reason, invalidation_level}
"""

import pandas as pd
from typing import Dict, Any, Optional


class MomentumAnalyst:
    def __init__(self, name: str = "Elena (Momentum Analyst)"):
        self.name = name

    def analyze(self, df_m15: pd.DataFrame) -> Dict[str, Any]:
        if df_m15.empty or len(df_m15) < 35:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 0,
                "reason": "Insufficient candles for RSI/MACD convergence calculation",
                "invalidation_level": 0.0
            }

        closes = df_m15["close"]
        lows = df_m15["low"]
        highs = df_m15["high"]
        last_close = float(closes.iloc[-1])

        # 1. RSI (14)
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss.replace(0, 0.00001)
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1])

        # 2. MACD (12, 26, 9)
        ema_12 = closes.ewm(span=12, adjust=False).mean()
        ema_26 = closes.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        hist = macd_line - signal_line
        curr_hist = float(hist.iloc[-1])
        prev_hist = float(hist.iloc[-2])

        # 3. Simple Divergence check on last 10 bars
        bullish_div = (lows.iloc[-1] < lows.iloc[-6]) and (rsi.iloc[-1] > rsi.iloc[-6])
        bearish_div = (highs.iloc[-1] > highs.iloc[-6]) and (rsi.iloc[-1] < rsi.iloc[-6])

        # 4. Bias evaluation
        if bullish_div or (current_rsi < 35 and curr_hist > prev_hist):
            bias = "BUY"
            confidence = 85 if bullish_div else 70
            reason = f"Bullish divergence / oversold reversal (RSI: {current_rsi:.1f}, MACD Hist rising)"
            invalidation = float(lows.tail(5).min())
        elif bearish_div or (current_rsi > 65 and curr_hist < prev_hist):
            bias = "SELL"
            confidence = 85 if bearish_div else 70
            reason = f"Bearish divergence / overbought exhaustion (RSI: {current_rsi:.1f}, MACD Hist falling)"
            invalidation = float(highs.tail(5).max())
        elif current_rsi > 52 and curr_hist > 0:
            bias = "BUY"
            confidence = 65
            reason = f"Bullish momentum expansion (RSI: {current_rsi:.1f} > 50, MACD positive)"
            invalidation = float(lows.tail(8).min())
        elif current_rsi < 48 and curr_hist < 0:
            bias = "SELL"
            confidence = 65
            reason = f"Bearish momentum expansion (RSI: {current_rsi:.1f} < 50, MACD negative)"
            invalidation = float(highs.tail(8).max())
        else:
            bias = "NEUTRAL"
            confidence = 45
            reason = f"Momentum flat / oscillator in neutral zone (RSI: {current_rsi:.1f})"
            invalidation = float(lows.tail(5).min())

        return {
            "agent": self.name,
            "bias": bias,
            "confidence": confidence,
            "reason": reason,
            "invalidation_level": round(invalidation, 2)
        }
