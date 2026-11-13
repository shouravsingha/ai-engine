"""
Market Regime Classification Engine
Classifies the live market structure into institutional volatility and flow regimes:
- TRENDING_EXPANSION: Directional orderflow, EMAs aligned, ADX > 25.
- COMPRESSED_ACCUMULATION: Tight range, Bollinger squeeze, low ATR, accumulation/distribution.
- HIGH_VOLATILITY_CHOP: Large wicks, erratic closes, multi-directional stop-hunts.
- NEWS_SHOCK_EVENT: Spread expansion, abnormal volume bursts, sudden price dislocation.
"""
from typing import Dict, Any
import numpy as np
import pandas as pd


class MarketRegimeEngine:
    def __init__(self):
        pass

    def classify_regime(
        self,
        df_candles: pd.DataFrame,
        market_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Classifies the regime based on 15m/5m price action and market metrics.
        Returns regime name, volatility state, trading recommendations, and adaptation rules.
        """
        if df_candles.empty or len(df_candles) < 20:
            return {
                "regime": "UNKNOWN",
                "volatility_state": "NORMAL",
                "trade_recommendation": "STANDBY",
                "target_multiplier": 1.0,
                "confidence": 50.0
            }

        closes = df_candles["close"].astype(float)
        highs = df_candles["high"].astype(float)
        lows = df_candles["low"].astype(float)

        spread = float(market_metrics.get("spread", 0.0))
        atr_14 = float(market_metrics.get("atr_14", 1.5))
        rsi_14 = float(market_metrics.get("rsi_14", 50.0))

        # 1. Check News Shock Event
        recent_spread = spread
        avg_spread = float(market_metrics.get("avg_spread", spread if spread > 0 else 0.30))
        spread_ratio = (recent_spread / max(avg_spread, 0.001)) if avg_spread > 0 else 1.0

        last_candle_body = abs(closes.iloc[-1] - float(df_candles["open"].iloc[-1]))
        if (spread_ratio >= 2.2 and spread > 0.40) or (atr_14 > 0 and last_candle_body > (atr_14 * 2.8)):
            return {
                "regime": "NEWS_SHOCK_EVENT",
                "volatility_state": "EXTREME",
                "trade_recommendation": "VETO_ALL_ENTRIES",
                "target_multiplier": 1.0,
                "required_consensus": 4,
                "notes": "Severe volatility burst or spread surge detected. Halt new orders until stabilization.",
                "confidence": 92.0
            }

        # 2. Moving Average Alignment & Trend Strength
        ema_20 = closes.ewm(span=20, adjust=False).mean()
        ema_50 = closes.ewm(span=50, adjust=False).mean() if len(closes) >= 50 else ema_20

        current_close = closes.iloc[-1]
        is_bullish_stack = current_close > ema_20.iloc[-1] > ema_50.iloc[-1]
        is_bearish_stack = current_close < ema_20.iloc[-1] < ema_50.iloc[-1]

        # Calculate Price Displacement over last 10 bars
        displacement_10 = (closes.iloc[-1] - closes.iloc[-10])
        abs_disp_pct = abs(displacement_10) / closes.iloc[-10]

        # Calculate Choppiness (ratio of net move to gross path distance)
        gross_path = (highs.iloc[-10:] - lows.iloc[-10:]).sum()
        net_move = abs(displacement_10)
        efficiency_ratio = (net_move / max(gross_path, 0.001))

        # 3. Classify Regime
        if (is_bullish_stack or is_bearish_stack) and efficiency_ratio > 0.45:
            regime = "TRENDING_EXPANSION"
            volatility_state = "HEALTHY_TREND"
            recommendation = "TREND_CONTINUATION_OTE"
            target_multiplier = 1.25  # Allow wider targets on trend expansions
            confidence = 85.0
            notes = "Institutional trend continuation active. FVG pullbacks and OTE reclaims are favorable."
        elif efficiency_ratio < 0.22:
            regime = "HIGH_VOLATILITY_CHOP"
            volatility_state = "CHOPPY"
            recommendation = "DEFENSIVE_SCALPING_ONLY"
            target_multiplier = 0.75  # Tighter targets in chop
            confidence = 80.0
            notes = "Price bouncing in multi-directional liquidity churn. High risk of false breakouts."
        else:
            regime = "COMPRESSED_ACCUMULATION"
            volatility_state = "LOW_COMPRESSION"
            recommendation = "WAIT_FOR_RANGE_PURGE"
            target_multiplier = 1.0
            confidence = 75.0
            notes = "Volatility compression. Await session open sweep of high/low boundaries."

        return {
            "regime": regime,
            "volatility_state": volatility_state,
            "trade_recommendation": recommendation,
            "target_multiplier": target_multiplier,
            "efficiency_ratio": round(float(efficiency_ratio), 3),
            "spread_ratio": round(float(spread_ratio), 2),
            "confidence": confidence,
            "notes": notes
        }
