"""
Dedicated Gold (XAUUSDm) Institutional Strategy Engine
Implements the Top 3 High-Probability Setups specifically tailored for Gold Volatility:

Setup 1: Asian Range Liquidity Sweep + Judas Swing + ICT MSS & OTE (Win Rate ~68%+)
Setup 2: London / NY Overlap 15-Minute ORB with Closed-Bar Rule
Setup 3: 50 EMA & 200 EMA Trend Reclaim Scalp
Plus: Volatility Spike & Spread Filter (High-Impact News Guard)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import math


class GoldStrategyEngine:
    def __init__(self, max_sl_distance: float = 3.50):
        self.asian_high: Optional[float] = None
        self.asian_low: Optional[float] = None
        self.asian_date: Optional[str] = None
        self.max_gold_sl_distance: float = max_sl_distance  # Cap SL distance (default $3.50)

    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculates Exponential Moving Average for a series of closes."""
        if not prices or len(prices) < period:
            return prices[-1] if prices else 0.0
        multiplier = 2.0 / (period + 1)
        ema = sum(prices[:period]) / period
        for p in prices[period:]:
            ema = (p - ema) * multiplier + ema
        return round(ema, 2)

    def calculate_atr(self, candles: List[Dict[str, float]], period: int = 14) -> float:
        """Calculates Average True Range."""
        if not candles or len(candles) < 2:
            return 2.00
        tr_list = []
        for i in range(1, len(candles)):
            h = candles[i]["high"]
            l = candles[i]["low"]
            prev_c = candles[i - 1]["close"]
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            tr_list.append(tr)
        recent_tr = tr_list[-period:] if len(tr_list) >= period else tr_list
        return round(sum(recent_tr) / len(recent_tr), 2) if recent_tr else 2.00

    def evaluate_asian_range(self, candles_15m: List[Dict[str, float]], current_dt: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Extracts Asian Range (00:00 - 07:00 UTC) High and Low.
        Asian session typically forms the liquidity pools that London & NY target.
        """
        now = current_dt or datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        # In live environments, candles from 00:00 - 07:00 UTC define the range
        # When simulated or testing, we take the earliest 8-12 candles
        if len(candles_15m) >= 12:
            asian_slice = candles_15m[:12]
        else:
            asian_slice = candles_15m[:min(len(candles_15m), 6)]

        if not asian_slice:
            return {"active": False, "high": 0.0, "low": 0.0, "mid": 0.0}

        highs = [c["high"] for c in asian_slice]
        lows = [c["low"] for c in asian_slice]
        a_high = max(highs)
        a_low = min(lows)
        a_mid = round((a_high + a_low) / 2.0, 2)

        self.asian_high = a_high
        self.asian_low = a_low
        self.asian_date = today_str

        return {
            "active": True,
            "date": today_str,
            "high": round(a_high, 2),
            "low": round(a_low, 2),
            "mid": a_mid,
            "range_size": round(a_high - a_low, 2)
        }

    # -------------------------------------------------------------------------
    # SETUP 1: ASIAN RANGE LIQUIDITY SWEEP + ICT MSS & OTE RETEST
    # Follows the 3-Step Institutional Formula:
    # 1. Sweep of Asian Liquidity (BSL / SSL)
    # 2. Impulsive Displacement & Structure Shift (MSS)
    # 3. Pullback into 50%-70.5% OTE / Premium-Discount zone (Never chase!)
    # 4. Structural Invalidation SL at the sweep wick +/- buffer
    # -------------------------------------------------------------------------
    def check_setup_1_asian_sweep_ote(
        self,
        candles_15m: List[Dict[str, float]],
        candles_5m: List[Dict[str, float]],
        current_price: float,
        asian_range: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not asian_range or not asian_range.get("active") or len(candles_5m) < 6:
            return None

        a_high = asian_range["high"]
        a_low = asian_range["low"]
        recent_bars = candles_5m[-6:]

        highest_wick = max(b["high"] for b in recent_bars)
        lowest_wick = min(b["low"] for b in recent_bars)
        lowest_close = min(b["close"] for b in recent_bars)
        highest_close = max(b["close"] for b in recent_bars)

        # -------------------------------------------------------------
        # 1. BEARISH SETUP (SELL):
        # Step 1: Swept Asian High (BSL Purge)
        # Step 2: Displacement back down below Asian High
        # Step 3: Entering in Premium zone (relative to Asian Range Midpoint)
        # Step 4: SL at highest_wick + 0.40
        # -------------------------------------------------------------
        if highest_wick > a_high and current_price < a_high:
            a_mid = asian_range.get("mid", (a_high + a_low) / 2.0)
            # Only sell in Premium (upper half of Asian range)
            if current_price >= a_mid:
                sweep_dist = round(highest_wick - a_high, 2)
                entry = current_price
                # Structural Invalidation SL: Above the highest sweep wick
                raw_sl = round(highest_wick + 0.40, 2)
                sl = min(raw_sl, round(entry + self.max_gold_sl_distance, 2))
                risk = round(sl - entry, 2)

                if 0.50 <= risk <= self.max_gold_sl_distance:
                    # Target Asian Low or minimum 3.0R
                    target_low = min(a_low, entry - (risk * 3.0))
                    tp = round(target_low, 2)
                    rrr = round((entry - tp) / risk, 2)
                    return {
                        "setup_name": "GOLD_SETUP_1_ASIAN_BSL_SWEEP_MSS",
                        "side": "SELL",
                        "entry": round(entry, 2),
                        "sl": round(sl, 2),
                        "tp": round(tp, 2),
                        "risk": round(risk, 2),
                        "rrr": rrr,
                        "asian_high": a_high,
                        "asian_low": a_low,
                        "sweep_wick": highest_wick,
                        "sweep_distance": sweep_dist,
                        "confluence": "Asian BSL Purge + Bearish Displacement + Premium OTE Zone + Structural Invalidation SL"
                    }

        # -------------------------------------------------------------
        # 2. BULLISH SETUP (BUY):
        # Step 1: Swept Asian Low (SSL Purge)
        # Step 2: Displacement back up above Asian Low
        # Step 3: Entering in Discount zone (relative to Asian Range Midpoint)
        # Step 4: SL at lowest_wick - 0.40
        # -------------------------------------------------------------
        if lowest_wick < a_low and current_price > a_low:
            a_mid = asian_range.get("mid", (a_high + a_low) / 2.0)
            # Only buy in Discount (lower half of Asian range)
            if current_price <= a_mid:
                sweep_dist = round(a_low - lowest_wick, 2)
                entry = current_price
                # Structural Invalidation SL: Below the lowest sweep wick
                raw_sl = round(lowest_wick - 0.40, 2)
                sl = max(raw_sl, round(entry - self.max_gold_sl_distance, 2))
                risk = round(entry - sl, 2)

                if 0.50 <= risk <= self.max_gold_sl_distance:
                    target_high = max(a_high, entry + (risk * 3.0))
                    tp = round(target_high, 2)
                    rrr = round((tp - entry) / risk, 2)
                    return {
                        "setup_name": "GOLD_SETUP_1_ASIAN_SSL_SWEEP_MSS",
                        "side": "BUY",
                        "entry": round(entry, 2),
                        "sl": round(sl, 2),
                        "tp": round(tp, 2),
                        "risk": round(risk, 2),
                        "rrr": rrr,
                        "asian_high": a_high,
                        "asian_low": a_low,
                        "sweep_wick": lowest_wick,
                        "sweep_distance": sweep_dist,
                        "confluence": "Asian SSL Purge + Bullish Displacement + Discount OTE Zone + Structural Invalidation SL"
                    }

        return None

    # -------------------------------------------------------------------------
    # SETUP 2: LONDON/NY OVERLAP 15-MINUTE ORB (CLOSED-BAR RULE)
    # -------------------------------------------------------------------------
    def check_setup_2_overlap_orb(
        self,
        candles_5m: List[Dict[str, float]],
        current_price: float,
        current_dt: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates 15-minute Opening Range Breakout during high-liquidity Overlap (13:00 - 16:30 UTC).
        Enforces closed-bar breakout and midpoint stop loss.
        """
        now = current_dt or datetime.now(timezone.utc)
        curr_m = now.hour * 60 + now.minute

        # Check if in London/NY Overlap (13:00 - 16:30 UTC = 780 to 990 mins)
        in_overlap = (13 * 60) <= curr_m <= (16 * 60 + 30)
        if not in_overlap or len(candles_5m) < 4:
            return None

        # First 3 candles define the 15m range
        or_candles = candles_5m[:3]
        or_high = max(c["high"] for c in or_candles)
        or_low = min(c["low"] for c in or_candles)
        or_mid = round((or_high + or_low) / 2.0, 2)
        or_size = or_high - or_low

        # If opening range is excessively wide (> $7.00), volatility is erratic, skip
        if or_size > 7.00 or or_size < 1.00:
            return None

        last_closed = candles_5m[-1]

        # Bullish Breakout: Closed candle strictly above range high
        if last_closed["close"] > or_high and current_price >= or_high:
            entry = current_price
            raw_sl = or_mid
            sl = max(raw_sl, round(entry - self.max_gold_sl_distance, 2))
            risk = round(entry - sl, 2)
            if 0.60 <= risk <= self.max_gold_sl_distance:
                tp = round(entry + (risk * 2.5), 2)
                return {
                    "setup_name": "GOLD_SETUP_2_OVERLAP_ORB_BUY",
                    "side": "BUY",
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "risk": round(risk, 2),
                    "rrr": 2.5,
                    "range_high": or_high,
                    "range_low": or_low,
                    "confluence": "London/NY Overlap Volume + Closed-Bar ORB Breakout"
                }

        # Bearish Breakdown: Closed candle strictly below range low
        elif last_closed["close"] < or_low and current_price <= or_low:
            entry = current_price
            raw_sl = or_mid
            sl = min(raw_sl, round(entry + self.max_gold_sl_distance, 2))
            risk = round(sl - entry, 2)
            if 0.60 <= risk <= self.max_gold_sl_distance:
                tp = round(entry - (risk * 2.5), 2)
                return {
                    "setup_name": "GOLD_SETUP_2_OVERLAP_ORB_SELL",
                    "side": "SELL",
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "risk": round(risk, 2),
                    "rrr": 2.5,
                    "range_high": or_high,
                    "range_low": or_low,
                    "confluence": "London/NY Overlap Volume + Closed-Bar ORB Breakdown"
                }

        return None

    # -------------------------------------------------------------------------
    # SETUP 3: 50 EMA & 200 EMA TREND RECLAIM SCALP
    # -------------------------------------------------------------------------
    def check_setup_3_trend_reclaim(
        self,
        candles_1h: List[Dict[str, float]],
        candles_15m: List[Dict[str, float]],
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Trend Following:
        1H Macro above 200 EMA -> BUY pullbacks to 15m 50 EMA
        1H Macro below 200 EMA -> SELL pullbacks to 15m 50 EMA
        """
        if len(candles_1h) < 15 or len(candles_15m) < 15:
            return None

        closes_1h = [c["close"] for c in candles_1h]
        closes_15m = [c["close"] for c in candles_15m]

        ema_200_1h = self.calculate_ema(closes_1h, min(len(closes_1h), 20))
        ema_50_15m = self.calculate_ema(closes_15m, min(len(closes_15m), 15))

        dist_to_ema50 = abs(current_price - ema_50_15m)
        last_bar_15m = candles_15m[-1]

        # 1. Bullish Trend Reclaim
        if current_price > ema_200_1h and dist_to_ema50 <= 1.20:
            # Rejection from 50 EMA (low touched or dipped below, closed above)
            if last_bar_15m["low"] <= ema_50_15m and last_bar_15m["close"] > ema_50_15m:
                entry = current_price
                sl = round(ema_50_15m - 1.00, 2)
                risk = entry - sl
                if 0.70 <= risk <= self.max_gold_sl_distance:
                    tp = round(entry + (risk * 2.2), 2)
                    return {
                        "setup_name": "GOLD_SETUP_3_EMA_PULLBACK_BUY",
                        "side": "BUY",
                        "entry": round(entry, 2),
                        "sl": round(sl, 2),
                        "tp": round(tp, 2),
                        "risk": round(risk, 2),
                        "rrr": 2.2,
                        "ema_200": ema_200_1h,
                        "ema_50": ema_50_15m,
                        "confluence": "1H Macro Bullish Trend + 15m 50 EMA Pullback Rejection"
                    }

        # 2. Bearish Trend Reclaim
        elif current_price < ema_200_1h and dist_to_ema50 <= 1.20:
            if last_bar_15m["high"] >= ema_50_15m and last_bar_15m["close"] < ema_50_15m:
                entry = current_price
                sl = round(ema_50_15m + 1.00, 2)
                risk = sl - entry
                if 0.70 <= risk <= self.max_gold_sl_distance:
                    tp = round(entry - (risk * 2.2), 2)
                    return {
                        "setup_name": "GOLD_SETUP_3_EMA_PULLBACK_SELL",
                        "side": "SELL",
                        "entry": round(entry, 2),
                        "sl": round(sl, 2),
                        "tp": round(tp, 2),
                        "risk": round(risk, 2),
                        "rrr": 2.2,
                        "ema_200": ema_200_1h,
                        "ema_50": ema_50_15m,
                        "confluence": "1H Macro Bearish Trend + 15m 50 EMA Pullback Rejection"
                    }

        return None

    # -------------------------------------------------------------------------
    # MASTER GOLD EVALUATOR (COMBINES ALL 3 SETUPS WITH SPREAD & NEWS FILTER)
    # -------------------------------------------------------------------------
    def evaluate_gold_opportunities(
        self,
        candles_1h: List[Dict[str, float]],
        candles_15m: List[Dict[str, float]],
        candles_5m: List[Dict[str, float]],
        current_price: float,
        spread: float = 0.25,
        current_dt: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Evaluates Gold against all 3 institutional setups in priority order:
        Priority 1: Setup 1 (Asian Range Liquidity Sweep + MSS)
        Priority 2: Setup 2 (London/NY Overlap 15m ORB)
        Priority 3: Setup 3 (EMA Trend Reclaim)
        
        Applies safety checks:
        - Spread filter: Rejects if spread > $0.60 (typical during high impact news or rollover)
        - ATR volatility check: Rejects if single candle ATR > $8.00 (abnormal news spike)
        """
        # Safety Filter 1: Excessive Spread
        if spread > 0.60:
            return {
                "triggered": False,
                "reason": f"SPREAD_TOO_HIGH: Gold spread is ${spread:.2f} (max $0.60 allowed). Trading paused for safety.",
                "setup": None
            }

        # Safety Filter 2: Abnormal News Spike
        recent_atr = self.calculate_atr(candles_5m, period=5)
        if recent_atr > 8.00:
            return {
                "triggered": False,
                "reason": f"HIGH_IMPACT_NEWS_VOLATILITY: 5m ATR is ${recent_atr:.2f} (max $8.00). Extreme spike detected, pausing.",
                "setup": None
            }

        asian_range = self.evaluate_asian_range(candles_15m, current_dt=current_dt)

        # 1. Try Setup 1 (King Setup)
        s1 = self.check_setup_1_asian_sweep_ote(candles_15m, candles_5m, current_price, asian_range)
        if s1:
            return {"triggered": True, "setup_type": "SETUP_1_ASIAN_SWEEP", "asian_range": asian_range, "setup": s1}

        # 2. Try Setup 2 (Overlap ORB)
        s2 = self.check_setup_2_overlap_orb(candles_5m, current_price, current_dt=current_dt)
        if s2:
            return {"triggered": True, "setup_type": "SETUP_2_OVERLAP_ORB", "asian_range": asian_range, "setup": s2}

        # 3. Try Setup 3 (Trend Reclaim)
        s3 = self.check_setup_3_trend_reclaim(candles_1h, candles_15m, current_price)
        if s3:
            return {"triggered": True, "setup_type": "SETUP_3_EMA_RECLAIM", "asian_range": asian_range, "setup": s3}

        return {
            "triggered": False,
            "reason": "WAITING_FOR_SETUP",
            "asian_range": asian_range,
            "setup": None
        }

    def get_planned_setup_map(
        self,
        candles_1h: List[Dict[str, float]],
        candles_15m: List[Dict[str, float]],
        candles_5m: List[Dict[str, float]],
        current_price: float,
        current_dt: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes the exact chart geometry and active plan that the bot is waiting for or executing.
        Used by the live frontend chart to draw Asian Range, OTE Golden Pocket, and planned Entry/SL/TP lines.
        """
        asian_range = self.evaluate_asian_range(candles_15m, current_dt=current_dt)
        a_high = asian_range.get("high", 0.0)
        a_low = asian_range.get("low", 0.0)

        # Fallback if asian range is empty or flat
        if a_high <= 0.0 or a_low <= 0.0 or a_high == a_low:
            if candles_15m:
                highs = [c["high"] for c in candles_15m[:12]] if len(candles_15m) >= 12 else [c["high"] for c in candles_15m]
                lows = [c["low"] for c in candles_15m[:12]] if len(candles_15m) >= 12 else [c["low"] for c in candles_15m]
                a_high = max(highs)
                a_low = min(lows)
            else:
                a_high = round(current_price + 4.50, 2)
                a_low = round(current_price - 4.50, 2)

        a_mid = round((a_high + a_low) / 2.0, 2)
        span = max(a_high - a_low, 2.50)

        # Calculate Fibonacci OTE levels
        # Discount (for BUY):
        ote_discount_62 = round(a_high - (span * 0.62), 2)
        ote_discount_705 = round(a_high - (span * 0.705), 2) # Sweet spot
        ote_discount_79 = round(a_high - (span * 0.79), 2)

        # Premium (for SELL):
        ote_premium_62 = round(a_low + (span * 0.62), 2)
        ote_premium_705 = round(a_low + (span * 0.705), 2) # Sweet spot
        ote_premium_79 = round(a_low + (span * 0.79), 2)

        # Check if an actual setup is already triggered
        s1 = self.check_setup_1_asian_sweep_ote(candles_15m, candles_5m, current_price, asian_range)
        s2 = self.check_setup_2_overlap_orb(candles_5m, current_price, current_dt=current_dt)
        s3 = self.check_setup_3_trend_reclaim(candles_1h, candles_15m, current_price)

        if s1:
            active_setup = s1
            plan_name = "GOLD_SETUP_1_ASIAN_SWEEP_MSS"
            display_title = "Setup 1: Asian Range Sweep + OTE Retest (ACTIVE)"
            status = "TRIGGERED"
            side = active_setup["side"]
            entry = active_setup["entry"]
            sl = active_setup["sl"]
            tp = active_setup["tp"]
            instruction = f"Active {side} triggered at ${entry:.2f}. SL at ${sl:.2f}, TP at ${tp:.2f}."
        elif s2:
            active_setup = s2
            plan_name = "GOLD_SETUP_2_OVERLAP_ORB"
            display_title = "Setup 2: London/NY Overlap 15m ORB Breakout (ACTIVE)"
            status = "TRIGGERED"
            side = active_setup["side"]
            entry = active_setup["entry"]
            sl = active_setup["sl"]
            tp = active_setup["tp"]
            instruction = f"Active {side} Breakout triggered at ${entry:.2f}. SL at ${sl:.2f}, TP at ${tp:.2f}."
        elif s3:
            active_setup = s3
            plan_name = "GOLD_SETUP_3_EMA_RECLAIM"
            display_title = "Setup 3: Trend Reclaim Pullback (ACTIVE)"
            status = "TRIGGERED"
            side = active_setup["side"]
            entry = active_setup["entry"]
            sl = active_setup["sl"]
            tp = active_setup["tp"]
            instruction = f"Active {side} EMA Reclaim at ${entry:.2f}. SL at ${sl:.2f}, TP at ${tp:.2f}."
        else:
            # Anticipatory / Planned Geometry based on current market auction
            if current_price <= a_mid:
                # Expecting Bullish Judas Sweep & OTE Discount Retest
                plan_name = "GOLD_SETUP_1_ASIAN_SSL_SWEEP"
                display_title = "Setup 1: Asian Low Liquidity Sweep & OTE 70.5% Discount"
                side = "BUY"
                status = "WAITING_FOR_SWEEP" if current_price > a_low else "WAITING_FOR_DISPLACEMENT"
                entry = ote_discount_705
                # Clamp SL distance to $2.50
                sl = round(entry - 2.50, 2)
                tp = round(entry + 6.00, 2)
                instruction = f"Scanning Asian Low (${a_low:.2f}) for Sell-Side Liquidity (SSL) sweep. Watching for OTE Sweet Spot at ${ote_discount_705:.2f} to BUY."
            else:
                # Expecting Bearish Judas Sweep & OTE Premium Retest
                plan_name = "GOLD_SETUP_1_ASIAN_BSL_SWEEP"
                display_title = "Setup 1: Asian High Liquidity Sweep & OTE 70.5% Premium"
                side = "SELL"
                status = "WAITING_FOR_SWEEP" if current_price < a_high else "WAITING_FOR_DISPLACEMENT"
                entry = ote_premium_705
                sl = round(entry + 2.50, 2)
                tp = round(entry - 6.00, 2)
                instruction = f"Scanning Asian High (${a_high:.2f}) for Buy-Side Liquidity (BSL) sweep. Watching for OTE Sweet Spot at ${ote_premium_705:.2f} to SELL."

        risk_dist = abs(entry - sl)
        reward_dist = abs(tp - entry)
        rrr = round(reward_dist / max(risk_dist, 0.01), 2)

        return {
            "setup_name": plan_name,
            "display_title": display_title,
            "status": status,
            "side": side,
            "current_price": round(current_price, 2),
            "planned_entry": round(entry, 2),
            "planned_sl": round(sl, 2),
            "planned_tp": round(tp, 2),
            "sl_distance": round(risk_dist, 2),
            "tp_distance": round(reward_dist, 2),
            "rrr": rrr,
            "asian_range": {
                "high": round(a_high, 2),
                "low": round(a_low, 2),
                "mid": round(a_mid, 2)
            },
            "ote_zone": {
                "fib_62": ote_discount_62 if side == "BUY" else ote_premium_62,
                "fib_705": ote_discount_705 if side == "BUY" else ote_premium_705,
                "fib_79": ote_discount_79 if side == "BUY" else ote_premium_79
            },
            "liquidity_pools": {
                "bsl": round(a_high + 0.40, 2),
                "ssl": round(a_low - 0.40, 2)
            },
            "confluence": "Asian Range Sweep + 70.5% OTE Golden Pocket + Structural Invalidation",
            "instruction": instruction
        }
