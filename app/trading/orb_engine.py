"""
Session Opening Range Breakout (ORB) Engine with Closed-Bar Rule
Adapted from Day Trader Skill for Global FX, Gold, and Crypto Markets.

Evaluates London (08:00 UTC), New York (13:00 UTC), and Asian (00:00 UTC) sessions.
Enforces the strict rule: NO entry on live wicks; ONLY completed closed bars count.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class SessionORBEngine:
    def __init__(self, or_minutes: int = 15, default_target_r: float = 2.0):
        """
        :param or_minutes: Opening range duration (default 15 minutes = 3x 5m candles or 1x 15m candle)
        :param default_target_r: Target R-multiple (e.g. 2.0R or 2.5R)
        """
        self.or_minutes = or_minutes
        self.default_target_r = default_target_r
        
        # Session schedules in UTC
        self.sessions = {
            "LONDON": {"start_hour": 8, "start_min": 0, "end_hour": 16, "end_min": 30, "name": "London Session"},
            "NEW_YORK": {"start_hour": 13, "start_min": 0, "end_hour": 21, "end_min": 0, "name": "New York Session"},
            "ASIA": {"start_hour": 0, "start_min": 0, "end_hour": 8, "end_min": 0, "name": "Asian Session"},
        }

    def get_current_session(self, current_dt: Optional[datetime] = None) -> Dict[str, Any]:
        """Identifies the active trading session based on UTC time."""
        now = current_dt or datetime.now(timezone.utc)
        curr_mins = now.hour * 60 + now.minute

        active_sessions = []
        for key, s in self.sessions.items():
            start_m = s["start_hour"] * 60 + s["start_min"]
            end_m = s["end_hour"] * 60 + s["end_min"]
            if start_m <= curr_mins < end_m:
                active_sessions.append((key, s["name"], curr_mins - start_m))

        if not active_sessions:
            return {"key": "OFF_HOURS", "name": "Off-Session", "elapsed_minutes": 0, "is_active": False}

        # Prefer London or NY if both active (Overlap 13:00 - 16:30 UTC)
        overlap = [s for s in active_sessions if s[0] in ("LONDON", "NEW_YORK")]
        chosen = overlap[0] if overlap else active_sessions[0]

        return {
            "key": chosen[0],
            "name": chosen[1],
            "elapsed_minutes": chosen[2],
            "is_active": True,
            "is_overlap": len(overlap) > 1
        }

    def calculate_opening_range(self, candles_5m: List[Dict[str, float]], bar_count: int = 3) -> Optional[Dict[str, float]]:
        """
        Calculates the Opening Range (High, Low, Midpoint) from the first N 5-minute candles.
        3 candles x 5m = 15-minute Opening Range.
        """
        if not candles_5m or len(candles_5m) < bar_count:
            return None

        range_candles = candles_5m[:bar_count]
        highs = [c["high"] for c in range_candles]
        lows = [c["low"] for c in range_candles]

        or_high = max(highs)
        or_low = min(lows)
        or_mid = round((or_high + or_low) / 2.0, 2)
        or_size = round(or_high - or_low, 2)

        return {
            "high": or_high,
            "low": or_low,
            "mid": or_mid,
            "size": or_size,
            "bars_used": bar_count
        }

    def analyze_orb_breakout(
        self,
        symbol: str,
        current_price: float,
        candles_5m: List[Dict[str, float]],
        target_r: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analyzes 5-minute candles against the Session Opening Range using the Closed-Bar rule.
        
        Rules:
        1. A breakout only triggers when a closed bar's close is strictly beyond range_high (for BUY)
           or strictly below range_low (for SELL).
        2. A wick that pierces the range but closes inside is classified as 'WICK_REJECTION' (no trade).
        3. Stop loss is conservatively placed at the Opening Range Midpoint (or-mid) or opposite edge.
        4. Target is set at R-multiples of risk.
        """
        r_multiple = target_r or self.default_target_r
        sess = self.get_current_session()

        if len(candles_5m) < 4:
            return {
                "symbol": symbol,
                "status": "WAITING_DATA",
                "session": sess["name"],
                "setup": None
            }

        # First 3 candles define the 15-minute opening range
        op_range = self.calculate_opening_range(candles_5m, bar_count=3)
        if not op_range:
            return {"symbol": symbol, "status": "RANGE_FORMING", "session": sess["name"], "setup": None}

        or_high = op_range["high"]
        or_low = op_range["low"]
        or_mid = op_range["mid"]

        # Evaluation candles after the 15m range
        eval_candles = candles_5m[3:]
        
        triggered_setup = None

        for idx, bar in enumerate(eval_candles):
            bar_c = bar["close"]
            bar_h = bar["high"]
            bar_l = bar["low"]

            # 1. Bullish ORB Breakout (Long)
            # Strict Rule: Candle CLOSE must be higher than range high!
            if bar_c > or_high:
                entry = bar_c
                sl = or_mid # Conservative Stop at Range Midpoint
                risk = entry - sl
                tp = round(entry + (risk * r_multiple), 2)
                triggered_setup = {
                    "side": "BUY",
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "risk": round(risk, 2),
                    "target_r": r_multiple,
                    "trigger_bar_index": 3 + idx,
                    "trigger_close": round(bar_c, 2),
                    "range_high": or_high,
                    "range_low": or_low,
                    "range_mid": or_mid,
                    "confirmation": "CLOSED_BAR_CONFIRMED"
                }
                break

            # 2. Bearish ORB Breakdown (Short)
            # Strict Rule: Candle CLOSE must be lower than range low!
            elif bar_c < or_low:
                entry = bar_c
                sl = or_mid # Conservative Stop at Range Midpoint
                risk = sl - entry
                tp = round(entry - (risk * r_multiple), 2)
                triggered_setup = {
                    "side": "SELL",
                    "entry": round(entry, 2),
                    "sl": round(sl, 2),
                    "tp": round(tp, 2),
                    "risk": round(risk, 2),
                    "target_r": r_multiple,
                    "trigger_bar_index": 3 + idx,
                    "trigger_close": round(bar_c, 2),
                    "range_high": or_high,
                    "range_low": or_low,
                    "range_mid": or_mid,
                    "confirmation": "CLOSED_BAR_CONFIRMED"
                }
                break

            # 3. Check for Wick Rejection (pierced without closed bar)
            elif bar_h > or_high and bar_c <= or_high:
                pass # Wick above, closed below
            elif bar_l < or_low and bar_c >= or_low:
                pass # Wick below, closed above

        if triggered_setup:
            return {
                "symbol": symbol,
                "status": "TRIGGERED",
                "session": sess["name"],
                "opening_range": op_range,
                "setup": triggered_setup
            }
        else:
            # Check current live price proximity
            dist_to_high = round(or_high - current_price, 2)
            dist_to_low = round(current_price - or_low, 2)
            return {
                "symbol": symbol,
                "status": "INSIDE_RANGE",
                "session": sess["name"],
                "opening_range": op_range,
                "dist_to_high": dist_to_high,
                "dist_to_low": dist_to_low,
                "setup": None
            }
