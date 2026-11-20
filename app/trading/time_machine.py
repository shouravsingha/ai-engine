"""
Time Machine Engine (Monte Carlo Probability Simulation)
Adapted from Day Trader Skill for MT5 Institutional Multi-Asset Trading (Gold, BTC, ETH, Forex).

Runs 2,000 - 10,000 Monte Carlo replays of market drift and candle permutations
before any live order touches Exness MT5. Supports both BUY (Long) and SELL (Short).
"""

import math
import random
from typing import Dict, Any, List, Optional

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


class TimeMachineEngine:
    def __init__(self, default_replays: int = 2500, horizon_bars: int = 36, seed: Optional[int] = 42):
        """
        :param default_replays: Number of Monte Carlo paths to simulate (2,500 is optimal for sub-50ms execution)
        :param horizon_bars: Forward bar horizon to check for resolution (36 x 5m = 3 hours)
        :param seed: Deterministic seed for reproducible tests; None for live entropy
        """
        self.default_replays = default_replays
        self.horizon_bars = horizon_bars
        self.seed = seed

    def build_ratio_pool_from_candles(self, candles: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Converts OHLC candles into relative ratio movements based on previous close:
        ratio = (open, high, low, close) / prev_close
        """
        if not candles or len(candles) < 3:
            return []

        pool = []
        for i in range(1, len(candles)):
            prev_c = candles[i - 1]["close"]
            if prev_c <= 0:
                continue
            curr = candles[i]
            pool.append({
                "open_ratio": curr["open"] / prev_c,
                "high_ratio": curr["high"] / prev_c,
                "low_ratio": curr["low"] / prev_c,
                "close_ratio": curr["close"] / prev_c,
            })
        return pool

    def fetch_mt5_candles(self, symbol: str, bar_count: int = 288) -> List[Dict[str, float]]:
        """
        Fetches M5 candles from MetaTrader 5 if terminal is available.
        288 M5 bars = 24 hours of live trading data.
        """
        candles = []
        if MT5_AVAILABLE:
            try:
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, bar_count)
                if rates is not None and len(rates) > 0:
                    for r in rates:
                        candles.append({
                            "open": float(r['open']),
                            "high": float(r['high']),
                            "low": float(r['low']),
                            "close": float(r['close']),
                            "volume": float(r['tick_volume'])
                        })
            except Exception:
                pass
        return candles

    def simulate_trade(
        self,
        symbol: str,
        side: str,
        entry: float,
        sl: float,
        tp: float,
        candles: Optional[List[Dict[str, float]]] = None,
        replays: Optional[int] = None,
        horizon_bars: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Simulates the proposed trade over N Monte Carlo paths.
        
        :param symbol: Asset symbol (e.g. 'XAUUSDm', 'BTCUSDm')
        :param side: 'BUY' or 'SELL'
        :param entry: Planned execution price
        :param sl: Stop loss price
        :param tp: Take profit price
        :param candles: Optional historical candle sequence. If omitted, attempts MT5 or synthetic calibration.
        :param replays: Number of simulation iterations
        :param horizon_bars: Number of future 5-minute bars to simulate
        :return: Comprehensive audit dictionary containing win/loss probabilities, expected R, and verdict.
        """
        side = side.upper()
        num_replays = replays or self.default_replays
        horizon = horizon_bars or self.horizon_bars
        rng = random.Random(self.seed) if self.seed is not None else random.Random()

        # Validate inputs
        if entry <= 0 or sl <= 0 or tp <= 0:
            return {"approved": False, "verdict": "INVALID_PRICES", "error": "Prices must be positive"}

        if side == "BUY":
            if sl >= entry or tp <= entry:
                return {"approved": False, "verdict": "INVALID_BUY_PLAN", "error": "For BUY, SL must be below entry and TP above"}
            risk = entry - sl
            reward = tp - entry
        elif side == "SELL":
            if sl <= entry or tp >= entry:
                return {"approved": False, "verdict": "INVALID_SELL_PLAN", "error": "For SELL, SL must be above entry and TP below"}
            risk = sl - entry
            reward = entry - tp
        else:
            return {"approved": False, "verdict": "INVALID_SIDE", "error": f"Unknown trade side: {side}"}

        target_r = round(reward / risk, 2) if risk > 0 else 0.0

        # Obtain candle pool
        if not candles:
            candles = self.fetch_mt5_candles(symbol, bar_count=200)

        # If candles still insufficient, construct calibrated baseline based on symbol volatility
        if not candles or len(candles) < 15:
            candles = self._generate_calibrated_candles(symbol, entry, count=60, rng=rng)

        ratio_pool = self.build_ratio_pool_from_candles(candles)
        if not ratio_pool:
            return {"approved": False, "verdict": "INSUFFICIENT_DATA", "error": "Cannot build price distribution pool"}

        target_hits = 0
        stop_hits = 0
        neither_hits = 0
        r_sum = 0.0

        # Run Monte Carlo loop
        for _ in range(num_replays):
            curr_price = entry
            outcome = "neither"
            outcome_r = 0.0

            for _ in range(horizon):
                step = rng.choice(ratio_pool)
                # Apply ratio variation
                bar_o = curr_price * step["open_ratio"]
                bar_h = curr_price * step["high_ratio"]
                bar_l = curr_price * step["low_ratio"]
                bar_c = curr_price * step["close_ratio"]
                curr_price = bar_c

                if side == "BUY":
                    # Conservative check: If bar touched both SL and TP, SL takes precedence
                    if bar_l <= sl:
                        outcome = "stop"
                        outcome_r = -1.0
                        break
                    elif bar_h >= tp:
                        outcome = "target"
                        outcome_r = target_r
                        break
                elif side == "SELL":
                    # Conservative check for SELL
                    if bar_h >= sl:
                        outcome = "stop"
                        outcome_r = -1.0
                        break
                    elif bar_l <= tp:
                        outcome = "target"
                        outcome_r = target_r
                        break

            if outcome == "target":
                target_hits += 1
                r_sum += outcome_r
            elif outcome == "stop":
                stop_hits += 1
                r_sum += outcome_r
            else:
                neither_hits += 1
                # Final open position R calculation at horizon end
                if side == "BUY":
                    neither_r = (curr_price - entry) / risk
                else:
                    neither_r = (entry - curr_price) / risk
                # Clamp within [-1.0, target_r]
                neither_r = max(-1.0, min(target_r, neither_r))
                r_sum += neither_r

        p_target = round((target_hits / num_replays) * 100, 1)
        p_stop = round((stop_hits / num_replays) * 100, 1)
        p_neither = round((neither_hits / num_replays) * 100, 1)
        expected_r = round(r_sum / num_replays, 3)

        # Break-even win rate required for this R:R: 1 / (1 + R)
        breakeven_p = (1.0 / (1.0 + target_r)) * 100.0 if (1.0 + target_r) > 0 else 50.0

        resolved_total = target_hits + stop_hits
        if resolved_total > 0:
            target_share = (target_hits / resolved_total) * 100.0
            edge = target_share - breakeven_p
        else:
            target_share = 50.0
            edge = 0.0

        # Verdict calculation
        # Hard Veto: Never approve a trade where stop probability dominates or target odds are too low
        if p_stop >= 60.0 or p_target < 25.0 or (p_stop > p_target * 1.5):
            verdict = "STRONG_STOP_BIAS" if p_stop >= 60.0 else "LEANS_STOP"
            approved = False
        elif edge >= 12.0 and expected_r > 0.15 and p_target >= p_stop:
            verdict = "STRONG_TARGET_EDGE"
            approved = True
        elif edge >= 4.0 and expected_r >= 0.0 and p_target >= (p_stop * 0.8):
            verdict = "LEANS_TARGET"
            approved = True
        elif abs(edge) < 4.0:
            verdict = "COIN_FLIP_NEUTRAL"
            # Require positive expectancy AND target odds at least equal to stop odds
            approved = (expected_r > 0.10 and p_target >= 40.0 and p_target >= p_stop)
        elif edge <= -12.0:
            verdict = "STRONG_STOP_BIAS"
            approved = False
        else:
            verdict = "LEANS_STOP"
            approved = False

        return {
            "symbol": symbol,
            "side": side,
            "entry": round(entry, 2),
            "sl": round(sl, 2),
            "tp": round(tp, 2),
            "target_r": target_r,
            "replays": num_replays,
            "horizon_bars": horizon,
            "prob_target_pct": p_target,
            "prob_stop_pct": p_stop,
            "prob_neither_pct": p_neither,
            "expected_r": expected_r,
            "breakeven_winrate_pct": round(breakeven_p, 1),
            "resolved_winrate_pct": round(target_share, 1),
            "edge_pct": round(edge, 1),
            "verdict": verdict,
            "approved": approved
        }

    def _generate_calibrated_candles(
        self,
        symbol: str,
        base_price: float,
        count: int = 60,
        rng: Optional[random.Random] = None
    ) -> List[Dict[str, float]]:
        """Calibrated realistic 5m candles based on asset characteristics."""
        r = rng or random.Random()
        vol_pct = 0.0015 if "XAU" in symbol else (0.0025 if "BTC" in symbol else 0.0008)
        candles = []
        curr = base_price
        for _ in range(count):
            change = (r.random() - 0.49) * 2 * (curr * vol_pct)
            o = curr
            c = curr + change
            h = max(o, c) + (abs(change) * r.random() * 0.8)
            l = min(o, c) - (abs(change) * r.random() * 0.8)
            candles.append({
                "open": round(o, 2),
                "high": round(h, 2),
                "low": round(l, 2),
                "close": round(c, 2),
                "volume": 100.0 + r.random() * 50.0
            })
            curr = c
        return candles
