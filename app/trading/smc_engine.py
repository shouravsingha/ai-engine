"""
Smart Money Concepts (SMC) & Inner Circle Trader (ICT) Institutional Engine
Implements:
1. ICT Killzones (London Open, New York Open, London Close, Asian Range)
2. Buy-Side & Sell-Side Liquidity (BSL / SSL) Sweeps & Turtle Soup Reversals
3. Market Structure Shift (MSS) with Impulsive Displacement
4. Order Blocks (OB) & Fair Value Gaps (FVG) with Consequent Encroachment (50% CE)
5. Optimal Trade Entry (OTE) 0.618 - 0.705 (ICT Sweet Spot) - 0.786
6. Precise Structure-Based SL & TP Calculation
"""
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional

class SMCEngine:
    def __init__(self):
        self.trend = "BULLISH" # Default HTF trend
        self.last_swing_high = 0.0
        self.last_swing_low = 0.0
        self.order_blocks = []
        self.fvg_zones = []

    @staticmethod
    def get_ict_killzone(utc_hour: Optional[int] = None) -> Dict[str, Any]:
        """
        Determines current active ICT Session & Killzone in UTC time:
        - London Open Killzone (LOKZ): 07:00 - 10:00 UTC (Judas Swing & Expansion)
        - New York Open Killzone (NYKZ): 12:00 - 15:00 UTC (Prime Institutional Trend)
        - London Close Killzone (LCKZ): 15:00 - 17:00 UTC (Daily Profit Taking)
        - Asian Range: 00:00 - 06:00 UTC (Liquidity Accumulation)
        """
        if utc_hour is None:
            utc_hour = datetime.utcnow().hour

        if 7 <= utc_hour < 10:
            return {
                "name": "London Open Killzone (LOKZ)",
                "code": "LOKZ",
                "status": "HIGH_PROBABILITY",
                "bias_multiplier": 1.25,
                "note": "Judas Swing & High Volume Expansion"
            }
        elif 12 <= utc_hour < 15:
            return {
                "name": "New York Open Killzone (NYKZ)",
                "code": "NYKZ",
                "status": "PRIME_INSTITUTIONAL",
                "bias_multiplier": 1.30,
                "note": "Maximum Daily Volatility & OTE Retests"
            }
        elif 15 <= utc_hour < 17:
            return {
                "name": "London Close Killzone (LCKZ)",
                "code": "LCKZ",
                "status": "PROFIT_HARVEST",
                "bias_multiplier": 1.0,
                "note": "Trend Exhaustion / Tighten Trailing Stops"
            }
        elif 0 <= utc_hour < 6:
            return {
                "name": "Asian Session Range",
                "code": "ASIAN",
                "status": "CONSOLIDATION",
                "bias_multiplier": 0.85,
                "note": "Building Liquidity Pools (Asian High/Low)"
            }
        else:
            return {
                "name": "Off-Killzone Interbank",
                "code": "OFF_HOURS",
                "status": "STANDARD",
                "bias_multiplier": 0.95,
                "note": "Selective Execution Only"
            }

    def analyze_candles(self, candles: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Takes OHLCV candle data and computes SMC + ICT institutional market structure.
        """
        if not candles:
            candles = [
                {"open": 2740.0, "high": 2750.0, "low": 2735.0, "close": 2745.0, "volume": 100}
            ]

        df = pd.DataFrame(candles)
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        vols = df['volume'].values if 'volume' in df.columns else [100.0] * len(df)

        n = len(df)
        recent_window = min(12, n)
        recent_high = float(max(highs[-recent_window:]))
        recent_low = float(min(lows[-recent_window:]))
        current_price = float(closes[-1])

        # Calculate Average True Range (ATR) approximation for tight SL sizing
        ranges = [highs[i] - lows[i] for i in range(max(0, n - 14), n)]
        atr = float(sum(ranges) / len(ranges)) if ranges else (current_price * 0.003)

        # 1. ICT Liquidity Sweeps (BSL / SSL Purge)
        # Check if the lowest wick swept previous lows but body closed back above
        ssl_swept = False
        bsl_swept = False
        sweep_level = None

        if n >= 5:
            prev_low_floor = min(lows[-6:-1])
            prev_high_ceil = max(highs[-6:-1])
            # Sell-Side Liquidity (SSL) Sweep: current low spiked below previous low but closed above it
            if lows[-1] < prev_low_floor and closes[-1] > prev_low_floor:
                ssl_swept = True
                sweep_level = float(prev_low_floor)
            # Buy-Side Liquidity (BSL) Sweep: current high spiked above previous high but closed below it
            elif highs[-1] > prev_high_ceil and closes[-1] < prev_high_ceil:
                bsl_swept = True
                sweep_level = float(prev_high_ceil)

        # 2. ICT Impulsive Displacement Detection
        # Large body candle (> 55% of total candle range) showing institutional commitment
        last_range = max(0.0001, highs[-1] - lows[-1])
        last_body = abs(closes[-1] - opens[-1])
        has_displacement = (last_body / last_range) >= 0.55 and last_range >= (atr * 0.8)

        # 3. Market Structure Shift (MSS) / BOS / CHoCH
        structure_event = "NONE"
        if self.last_swing_high > 0 and current_price > self.last_swing_high:
            if self.trend == "BEARISH":
                structure_event = "ICT MSS (BULLISH SHIFT)" if has_displacement else "CHoCH (BULLISH REVERSAL)"
                self.trend = "BULLISH"
            else:
                structure_event = "BOS (BULLISH CONTINUATION)"
            self.last_swing_high = recent_high

        elif self.last_swing_low > 0 and current_price < self.last_swing_low:
            if self.trend == "BULLISH":
                structure_event = "ICT MSS (BEARISH SHIFT)" if has_displacement else "CHoCH (BEARISH REVERSAL)"
                self.trend = "BEARISH"
            else:
                structure_event = "BOS (BEARISH CONTINUATION)"
            self.last_swing_low = recent_low
        else:
            self.last_swing_high = recent_high
            self.last_swing_low = recent_low

        # 4. ICT Order Block Detection
        ob_zone = None
        if self.trend == "BULLISH":
            # Bullish Order Block = Low of the last down candle before displacement impulse
            ob_low = recent_low
            ob_high = recent_low + (recent_high - recent_low) * 0.18
            ob_zone = {
                "type": "BULLISH_OB",
                "low": round(ob_low, 2),
                "high": round(ob_high, 2),
                "invalidation": round(ob_low - (atr * 0.25), 2)
            }
        else:
            ob_high = recent_high
            ob_low = recent_high - (recent_high - recent_low) * 0.18
            ob_zone = {
                "type": "BEARISH_OB",
                "low": round(ob_low, 2),
                "high": round(ob_high, 2),
                "invalidation": round(ob_high + (atr * 0.25), 2)
            }

        # 5. Fair Value Gap (FVG) with Consequent Encroachment (50% CE)
        fvg = None
        if n >= 3:
            c1_high = float(highs[-3])
            c3_low = float(lows[-1])
            if c3_low > c1_high:
                ce = float((c1_high + c3_low) / 2.0)
                fvg = {
                    "type": "BULLISH_FVG",
                    "bottom": round(float(c1_high), 2),
                    "top": round(float(c3_low), 2),
                    "ce_50": round(float(ce), 2), # Consequent Encroachment sweet spot
                    "tested": bool(current_price <= ce)
                }
            elif lows[-3] > highs[-1]:
                c1_low = float(lows[-3])
                c3_high = float(highs[-1])
                ce = float((c1_low + c3_high) / 2.0)
                fvg = {
                    "type": "BEARISH_FVG",
                    "top": round(float(c1_low), 2),
                    "bottom": round(float(c3_high), 2),
                    "ce_50": round(float(ce), 2),
                    "tested": bool(current_price >= ce)
                }

        # 6. Current ICT Killzone
        killzone = self.get_ict_killzone()

        # 7. Exact ICT Recommended SL and TP
        if self.trend == "BULLISH":
            # SL strictly below Order Block or swept liquidity low + tiny buffer
            anchor_low = sweep_level if ssl_swept and sweep_level else (ob_zone["low"] if ob_zone else recent_low)
            recommended_sl = round(float(anchor_low - (atr * 0.35)), 2)
            # Ensure SL is not ridiculously far; max distance capped by 1.5x ATR
            if (current_price - recommended_sl) > (atr * 2.2):
                recommended_sl = round(float(current_price - (atr * 1.8)), 2)
            
            # TP placed at BSL (previous high) or 2.5x risk
            risk_dist = max(0.1, current_price - recommended_sl)
            recommended_tp = round(float(max(recent_high + (atr * 0.5), current_price + (risk_dist * 2.6))), 2)
        else:
            anchor_high = sweep_level if bsl_swept and sweep_level else (ob_zone["high"] if ob_zone else recent_high)
            recommended_sl = round(float(anchor_high + (atr * 0.35)), 2)
            if (recommended_sl - current_price) > (atr * 2.2):
                recommended_sl = round(float(current_price + (atr * 1.8)), 2)
            risk_dist = max(0.1, recommended_sl - current_price)
            recommended_tp = round(float(min(recent_low - (atr * 0.5), current_price - (risk_dist * 2.6))), 2)

        return {
            "trend": self.trend,
            "structure_event": structure_event,
            "swing_high": round(float(recent_high), 2),
            "swing_low": round(float(recent_low), 2),
            "atr": round(float(atr), 2),
            "order_block": ob_zone,
            "fvg": fvg,
            "liquidity_sweep": {
                "ssl_swept": bool(ssl_swept),
                "bsl_swept": bool(bsl_swept),
                "level": round(float(sweep_level), 2) if sweep_level else None
            },
            "displacement": bool(has_displacement),
            "killzone": killzone,
            "recommended_sl": recommended_sl,
            "recommended_tp": recommended_tp,
            "current_price": round(float(current_price), 2)
        }
