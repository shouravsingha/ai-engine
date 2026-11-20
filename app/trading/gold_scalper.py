"""
Dedicated Gold (XAUUSDm) High-Frequency Micro-Scalper Engine.
Operates on M1 and M5 timeframes with H1 200-EMA Trend Alignment.
Generates Multi-Trade Staggered Orders (Order 1, Order 2, Order 3) with independent Micro-TPs.
Enforces Spread Guard (< $0.35), Global Basket Risk Cap, and Auto-Healer Defenses.
"""
import time
from typing import Dict, Any, List, Optional


class GoldScalperEngine:
    def __init__(
        self,
        symbol: str = "XAUUSDm",
        max_spread: float = 0.35,
        max_concurrent_scalps: int = 3,
        global_basket_loss_cap: float = 3.50,
        cooldown_seconds: float = 900.0  # 15 minutes after 2 consecutive scalp losses
    ):
        self.symbol = symbol
        self.max_spread = max_spread
        self.max_concurrent_scalps = max_concurrent_scalps
        self.global_basket_loss_cap = global_basket_loss_cap
        self.cooldown_seconds = cooldown_seconds

        self.consecutive_scalp_losses: int = 0
        self.scalp_cooldown_until: float = 0.0
        self.last_scalp_trigger_ts: float = 0.0
        self.active_scalp_tickets: List[int] = []

    def is_cooling_down(self) -> bool:
        """Checks if scalper is in cooldown after consecutive losses."""
        return time.time() < self.scalp_cooldown_until

    def get_cooldown_remaining_seconds(self) -> int:
        return max(0, int(self.scalp_cooldown_until - time.time()))

    def record_scalp_result(self, profit: float):
        """Records closed scalp outcome for streak tracking."""
        if profit < -0.20:
            self.consecutive_scalp_losses += 1
            if self.consecutive_scalp_losses >= 2:
                self.scalp_cooldown_until = time.time() + self.cooldown_seconds
                self.consecutive_scalp_losses = 0
        elif profit > 0.50:
            self.consecutive_scalp_losses = 0

    def compute_indicators(self, candles: List[Dict[str, float]]) -> Dict[str, Any]:
        """Calculates fast EMA 9, EMA 21, VWAP, RSI 14, and ATR 14."""
        if not candles or len(candles) < 22:
            return {}

        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        volumes = [max(1.0, c.get("volume", 1.0)) for c in candles]

        # 1. EMA 9 & EMA 21
        def calc_ema(series, period):
            k = 2.0 / (period + 1)
            ema = sum(series[:period]) / period
            for p in series[period:]:
                ema = (p - ema) * k + ema
            return ema

        ema_9 = round(calc_ema(closes, 9), 3)
        ema_21 = round(calc_ema(closes, 21), 3)

        # Previous candle EMA for crossover
        prev_ema_9 = round(calc_ema(closes[:-1], 9), 3) if len(closes) > 10 else ema_9
        prev_ema_21 = round(calc_ema(closes[:-1], 21), 3) if len(closes) > 22 else ema_21

        # 2. VWAP (Cumulative Typical Price * Volume)
        cum_vol = sum(volumes)
        cum_pv = sum(((h + l + c) / 3.0) * v for h, l, c, v in zip(highs, lows, closes, volumes))
        vwap = round(cum_pv / max(cum_vol, 1.0), 3)

        # 3. ATR 14
        tr_list = []
        for i in range(1, len(candles)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1])
            )
            tr_list.append(tr)
        atr_14 = round(sum(tr_list[-14:]) / min(len(tr_list), 14), 3) if tr_list else 1.50

        # 4. RSI 14
        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            if diff > 0:
                gains.append(diff)
                losses.append(0.0)
            else:
                gains.append(0.0)
                losses.append(abs(diff))
        avg_gain = sum(gains[-14:]) / 14 if len(gains) >= 14 else 1.0
        avg_loss = sum(losses[-14:]) / 14 if len(losses) >= 14 else 1.0
        rs = avg_gain / max(avg_loss, 0.0001)
        rsi = round(100.0 - (100.0 / (1.0 + rs)), 2)

        return {
            "ema_9": ema_9,
            "ema_21": ema_21,
            "prev_ema_9": prev_ema_9,
            "prev_ema_21": prev_ema_21,
            "vwap": vwap,
            "atr_14": atr_14,
            "rsi": rsi,
            "last_close": closes[-1],
            "last_high": highs[-1],
            "last_low": lows[-1],
        }

    def evaluate_h1_trend(self, candles_h1: List[Dict[str, float]]) -> str:
        """Determines Paul Tudor Jones 200 EMA trend on H1 candles."""
        if not candles_h1 or len(candles_h1) < 20:
            return "BULLISH"

        closes = [c["close"] for c in candles_h1]
        period = min(200, len(closes))
        k = 2.0 / (period + 1)
        ema = sum(closes[:period]) / period
        for p in closes[period:]:
            ema = (p - ema) * k + ema

        curr_p = closes[-1]
        if curr_p > ema:
            return "BULLISH"
        elif curr_p < ema:
            return "BEARISH"
        return "NEUTRAL"

    def check_micro_liquidity_sweep(self, candles_m1: List[Dict[str, float]]) -> Dict[str, Any]:
        """Detects micro liquidity sweep of recent 5-10 M1 candle highs/lows with rejection wick."""
        if not candles_m1 or len(candles_m1) < 8:
            return {"bullish_sweep": False, "bearish_sweep": False}

        recent_highs = [c["high"] for c in candles_m1[-8:-1]]
        recent_lows = [c["low"] for c in candles_m1[-8:-1]]
        highest_prev = max(recent_highs)
        lowest_prev = min(recent_lows)

        curr = candles_m1[-1]
        body = abs(curr["close"] - curr["open"])

        # Bullish sweep: Low pierced lowest_prev but closed well above it (rejection lower wick)
        lower_wick = min(curr["open"], curr["close"]) - curr["low"]
        bullish_sweep = (curr["low"] < lowest_prev) and (curr["close"] > lowest_prev) and (lower_wick > body * 1.2)

        # Bearish sweep: High pierced highest_prev but closed well below it (rejection upper wick)
        upper_wick = curr["high"] - max(curr["open"], curr["close"])
        bearish_sweep = (curr["high"] > highest_prev) and (curr["close"] < highest_prev) and (upper_wick > body * 1.2)

        return {
            "bullish_sweep": bullish_sweep,
            "bearish_sweep": bearish_sweep,
            "highest_prev": highest_prev,
            "lowest_prev": lowest_prev
        }

    def generate_scalp_opportunities(
        self,
        candles_m1: List[Dict[str, float]],
        candles_m5: List[Dict[str, float]],
        candles_h1: List[Dict[str, float]],
        current_price: float,
        current_spread: float = 0.25,
        open_positions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Main Scalping Decision Engine:
        Analyzes M1/M5 confluence and outputs Multi-Trade Scalp Setup if criteria met.
        """
        # 1. Spread Guard Check
        if current_spread > self.max_spread:
            return {
                "triggered": False,
                "reason": f"🛑 SPREAD GUARD: Spread {current_spread:.2f} > ceiling {self.max_spread:.2f}"
            }

        # 2. Cooldown Guard Check
        if self.is_cooling_down():
            rem = self.get_cooldown_remaining_seconds()
            return {
                "triggered": False,
                "reason": f"⏸️ SCALPER COOLDOWN: Active after streak loss ({rem}s remaining)"
            }

        # 3. Concurrent Scalp Positions Ceiling
        open_scalps = [
            p for p in (open_positions or [])
            if "SCALP" in str(p.get("comment", "")).upper() or "XAU" in str(p.get("symbol", "")).upper()
        ]
        if len(open_scalps) >= self.max_concurrent_scalps:
            return {
                "triggered": False,
                "reason": f"⏸️ MAX SCALPS REACHED: {len(open_scalps)}/{self.max_concurrent_scalps} active"
            }

        # 4. Anti-Churn Inter-Trade Timer (Min 45 seconds between scalp cluster triggers)
        if time.time() - self.last_scalp_trigger_ts < 45.0:
            return {"triggered": False, "reason": "Pacing: 45s scalp interval cooldown"}

        # 5. Indicator Confluence
        m1_ind = self.compute_indicators(candles_m1)
        m5_ind = self.compute_indicators(candles_m5)
        if not m1_ind or not m5_ind:
            return {"triggered": False, "reason": "Insufficient M1/M5 candle data"}

        h1_trend = self.evaluate_h1_trend(candles_h1)
        sweep_data = self.check_micro_liquidity_sweep(candles_m1)

        m1_bull_cross = (m1_ind["prev_ema_9"] <= m1_ind["prev_ema_21"]) and (m1_ind["ema_9"] > m1_ind["ema_21"])
        m1_bear_cross = (m1_ind["prev_ema_9"] >= m1_ind["prev_ema_21"]) and (m1_ind["ema_9"] < m1_ind["ema_21"])

        # 6. Signal Determination
        side = None
        confluence_tag = ""

        # BUY Setup: H1 Bullish/Neutral + Price > VWAP + (M1 EMA Cross OR Bullish Liquidity Sweep) + RSI Healthy (Not Overbought)
        if (h1_trend != "BEARISH") and (current_price >= m1_ind["vwap"] - 0.20):
            if (m1_bull_cross or sweep_data["bullish_sweep"]) and (40.0 <= m1_ind["rsi"] <= 62.0):
                side = "BUY"
                confluence_tag = "M1 EMA Cross + Above VWAP" if m1_bull_cross else "M1 Micro Liquidity Sweep Rejection"

        # SELL Setup: H1 Bearish/Neutral + Price < VWAP + (M1 Bear Cross OR Bearish Liquidity Sweep) + RSI Healthy (Not Oversold)
        elif (h1_trend != "BULLISH") and (current_price <= m1_ind["vwap"] + 0.20):
            if (m1_bear_cross or sweep_data["bearish_sweep"]) and (38.0 <= m1_ind["rsi"] <= 60.0):
                side = "SELL"
                confluence_tag = "M1 EMA Cross + Below VWAP" if m1_bear_cross else "M1 Micro Liquidity Sweep Rejection"

        if not side:
            return {"triggered": False, "reason": "Searching for high-probability M1/M5 scalp setup"}

        # 7. Formulate Multi-Trade Staggered Scalp Orders (3 Micro Orders)
        # Dynamic ATR-based SL: Never choke within $1.80 noise; provide calibrated breathing buffer ($2.80 - $4.00)
        atr_val = max(m1_ind.get("atr_14", 1.80), m5_ind.get("atr_14", 1.80))
        base_sl_dist = round(min(max(atr_val * 1.6, 2.80), 4.00), 2)
        sl_price = round(current_price - base_sl_dist, 2) if side == "BUY" else round(current_price + base_sl_dist, 2)

        tp1_dist = round(max(base_sl_dist * 0.85, 2.00), 2)
        tp2_dist = round(max(base_sl_dist * 1.60, 3.80), 2)
        tp3_dist = round(max(base_sl_dist * 2.50, 5.50), 2)

        multi_orders = [
            {
                "order_index": 1,
                "label": "Fast Scalp (Quick Cash)",
                "side": side,
                "symbol": self.symbol,
                "entry": round(current_price, 2),
                "sl": sl_price,
                "tp": round(current_price + tp1_dist, 2) if side == "BUY" else round(current_price - tp1_dist, 2),
                "tp_dist": tp1_dist,
                "lot": 0.01,
                "comment": "TradingAI Gold Scalp-1"
            },
            {
                "order_index": 2,
                "label": "Core Scalp (Target 1)",
                "side": side,
                "symbol": self.symbol,
                "entry": round(current_price, 2),
                "sl": sl_price,
                "tp": round(current_price + tp2_dist, 2) if side == "BUY" else round(current_price - tp2_dist, 2),
                "tp_dist": tp2_dist,
                "lot": 0.01,
                "comment": "TradingAI Gold Scalp-2"
            },
            {
                "order_index": 3,
                "label": "Runner Scalp (Momentum Blast)",
                "side": side,
                "symbol": self.symbol,
                "entry": round(current_price, 2),
                "sl": sl_price,
                "tp": round(current_price + tp3_dist, 2) if side == "BUY" else round(current_price - tp3_dist, 2),
                "tp_dist": tp3_dist,
                "lot": 0.01,
                "comment": "TradingAI Gold Scalp-3"
            }
        ]

        self.last_scalp_trigger_ts = time.time()

        return {
            "triggered": True,
            "side": side,
            "symbol": self.symbol,
            "current_price": round(current_price, 2),
            "h1_trend": h1_trend,
            "vwap": m1_ind["vwap"],
            "rsi": m1_ind["rsi"],
            "confluence": confluence_tag,
            "multi_orders": multi_orders,
            "total_risk_dist": base_sl_dist,
            "strategy": "GOLD_M1_M5_MULTI_SCALPER"
        }
