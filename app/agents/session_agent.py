"""
Volatility & Session Analyst Specialist Agent.
Monitors ATR volatility expansion, Session killzones, and High-Impact Economic News Windows.
Output format: {bias, confidence (0-100), reason, invalidation_level}
"""

import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class SessionVolatilityAnalyst:
    def __init__(self, name: str = "Kai (Volatility/Session Scout)"):
        self.name = name

    def analyze(self, df_m15: pd.DataFrame, session_info: Dict[str, Any], news_blackout: bool = False) -> Dict[str, Any]:
        if df_m15.empty or len(df_m15) < 15:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 0,
                "reason": "Insufficient candles for volatility check",
                "invalidation_level": 0.0
            }

        highs = df_m15["high"]
        lows = df_m15["low"]
        closes = df_m15["close"]

        # 1. ATR (14) Volatility calculation
        tr1 = highs - lows
        tr2 = (highs - closes.shift(1)).abs()
        tr3 = (lows - closes.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = float(tr.rolling(14).mean().iloc[-1])
        recent_candle_range = float((highs.iloc[-1] - lows.iloc[-1]))

        is_expanding = recent_candle_range > (atr_14 * 1.25)
        session_name = session_info.get("session", "UNKNOWN")
        is_killzone = session_info.get("is_killzone", False)

        # 2. News Blackout Rule: Reject all trade setups
        if news_blackout:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 0,
                "reason": "🚨 HIGH-IMPACT NEWS BLACKOUT: Extreme volatility window active. Trading prohibited.",
                "invalidation_level": 0.0
            }

        # 3. Session Volatility Guidance
        if is_killzone and is_expanding:
            confidence = 85
            bias = "BUY" if closes.iloc[-1] > opens_val else "SELL" if 'opens_val' in locals() else ("BUY" if closes.iloc[-1] > closes.iloc[-2] else "SELL")
            reason = f"Session Killzone ({session_name}) active with expanding ATR ({atr_14:.2f})"
            invalidation = float(lows.iloc[-1] if bias == "BUY" else highs.iloc[-1])
        elif is_killzone:
            confidence = 70
            bias = "BUY" if closes.iloc[-1] > closes.iloc[-2] else "SELL"
            reason = f"Active {session_name} Session flow. Volatility within standard distribution."
            invalidation = float(lows.tail(3).min() if bias == "BUY" else highs.tail(3).max())
        else:
            confidence = 40
            bias = "NEUTRAL"
            reason = f"Low liquidity off-hours session ({session_name}). Consolidation bias."
            invalidation = float(lows.tail(5).min())

        return {
            "agent": self.name,
            "bias": bias,
            "confidence": confidence,
            "reason": reason,
            "invalidation_level": round(invalidation, 2)
        }
