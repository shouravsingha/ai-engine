"""
MT5 Multi-Timeframe Data Collector & Session Intelligence Engine.
Pulls OHLCV (M1, M5, M15, H1, H4, D1), spread, volume, detects session phases,
and stores high-fidelity records into the local SQLite database.
"""

import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd

from app.data.db_manager import DatabaseManager

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False


TIMEFRAME_MAP = {}
if MT5_AVAILABLE:
    TIMEFRAME_MAP = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }


class DataCollector:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()
        self.watched_symbols = ["XAUUSDm", "BTCUSDm", "EURUSDm", "GBPUSDm"]
        self.timeframes = ["M1", "M5", "M15", "H1", "H4", "D1"]
        self.high_impact_news_window = 30  # minutes before and after high-impact news

    def get_current_session(self) -> Dict[str, Any]:
        """
        Determines active trading session in UTC time:
        - Asian: 00:00 - 08:00 UTC
        - London: 07:00 - 16:00 UTC
        - New York: 13:00 - 21:00 UTC
        - London/NY Overlap (Killzone): 13:00 - 16:00 UTC
        """
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour

        active_sessions = []
        is_overlap = False

        if 0 <= hour < 8:
            active_sessions.append("ASIAN")
        if 7 <= hour < 16:
            active_sessions.append("LONDON")
        if 13 <= hour < 21:
            active_sessions.append("NEW_YORK")

        if "LONDON" in active_sessions and "NEW_YORK" in active_sessions:
            is_overlap = True

        session_name = "OVERLAP (LONDON-NY)" if is_overlap else ("-".join(active_sessions) if active_sessions else "OFF_HOURS")

        return {
            "session": session_name,
            "hour_utc": hour,
            "minute_utc": now_utc.minute,
            "is_killzone": is_overlap or (hour in [7, 8, 13, 14, 15]),
            "timestamp": int(now_utc.timestamp()),
            "datetime_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S")
        }

    def fetch_rates_mt5(self, symbol: str, timeframe: str, count: int = 100) -> List[Dict[str, Any]]:
        """Fetches OHLCV rates directly from MT5 terminal."""
        if not MT5_AVAILABLE or timeframe not in TIMEFRAME_MAP:
            return []

        try:
            tf_const = TIMEFRAME_MAP[timeframe]
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, count)
            if rates is None or len(rates) == 0:
                return []

            cleaned = []
            for r in rates:
                cleaned.append({
                    "time": int(r['time']),
                    "open": float(r['open']),
                    "high": float(r['high']),
                    "low": float(r['low']),
                    "close": float(r['close']),
                    "tick_volume": int(r['tick_volume']),
                    "spread": int(r['spread'])
                })
            return cleaned
        except Exception as e:
            print(f"[DATA_COLLECTOR] Error fetching {symbol} {timeframe}: {e}")
            return []

    def sync_all_symbols(self, count: int = 150) -> Dict[str, int]:
        """Pulls OHLCV across all watched symbols and timeframes, storing in SQLite."""
        stats = {}
        for sym in self.watched_symbols:
            total_stored = 0
            for tf in self.timeframes:
                rates = self.fetch_rates_mt5(sym, tf, count=count)
                if rates:
                    stored = self.db.store_candles(sym, tf, rates)
                    total_stored += stored
            stats[sym] = total_stored
        return stats

    def get_symbol_metrics(self, symbol: str) -> Dict[str, Any]:
        """Extracts current spread, tick volume, and latest price action."""
        session_info = self.get_current_session()
        spread = 0.0
        bid = 0.0
        ask = 0.0

        if MT5_AVAILABLE:
            try:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    bid = float(tick.bid)
                    ask = float(tick.ask)
                    spread = round(ask - bid, 4)
            except Exception:
                pass

        # Compute technical features from M15 stored candles
        df_m15 = self.db.get_candles_df(symbol, "M15", limit=50)
        atr_14 = 0.0
        rsi_14 = 50.0
        ema_20 = 0.0
        ema_50 = 0.0
        ema_200 = 0.0

        if not df_m15.empty and len(df_m15) >= 15:
            closes = df_m15["close"]
            highs = df_m15["high"]
            lows = df_m15["low"]

            # EMA
            ema_20 = round(float(closes.ewm(span=20, adjust=False).mean().iloc[-1]), 4)
            if len(df_m15) >= 50:
                ema_50 = round(float(closes.ewm(span=50, adjust=False).mean().iloc[-1]), 4)
                ema_200 = round(float(closes.ewm(span=200, adjust=False).mean().iloc[-1]), 4)

            # ATR (True Range)
            tr1 = highs - lows
            tr2 = (highs - closes.shift(1)).abs()
            tr3 = (lows - closes.shift(1)).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_14 = round(float(tr.rolling(14).mean().iloc[-1]), 4)

            # RSI
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss.replace(0, 0.00001)
            rsi_val = 100 - (100 / (1 + rs))
            if not pd.isna(rsi_val.iloc[-1]):
                rsi_14 = round(float(rsi_val.iloc[-1]), 2)

        metrics = {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "session": session_info["session"],
            "is_killzone": session_info["is_killzone"],
            "atr_14": atr_14,
            "rsi_14": rsi_14,
            "ema_20": ema_20,
            "ema_50": ema_50,
            "ema_200": ema_200,
            "timestamp": int(datetime.now(timezone.utc).timestamp())
        }
        return metrics
