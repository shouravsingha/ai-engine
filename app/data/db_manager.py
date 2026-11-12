"""
Institutional SQLite Database Manager for Human-Like Trading Desk.
Handles multi-timeframe OHLCV storage, market metrics, economic calendar,
decision logging, trade journal, and daily automated backups.
"""

import os
import sqlite3
import json
import shutil
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
DB_PATH = os.path.join(DB_DIR, "trading_desk.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "backups")


class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes tables for candles, metrics, decisions, and trades."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Multi-Timeframe OHLCV Candles
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candles (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                datetime_utc TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                tick_volume INTEGER NOT NULL,
                spread INTEGER DEFAULT 0,
                PRIMARY KEY (symbol, timeframe, timestamp)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candles_lookup ON candles (symbol, timeframe, timestamp DESC)")

            # 2. Market Metrics Snapshot
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                datetime_utc TEXT NOT NULL,
                spread REAL,
                tick_volume INTEGER,
                session TEXT,
                atr_14 REAL,
                rsi_14 REAL,
                ema_20 REAL,
                ema_50 REAL,
                ema_200 REAL,
                adx_14 REAL
            )
            """)

            # 3. Economic Calendar Events
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id TEXT PRIMARY KEY,
                timestamp INTEGER NOT NULL,
                datetime_utc TEXT NOT NULL,
                currency TEXT NOT NULL,
                event_name TEXT NOT NULL,
                impact TEXT NOT NULL, -- HIGH, MEDIUM, LOW
                forecast TEXT,
                previous TEXT,
                actual TEXT
            )
            """)

            # 4. Decision Desk Journal (Pre-Trade Audit)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp INTEGER NOT NULL,
                datetime_utc TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                consensus_bias TEXT NOT NULL, -- BUY, SELL, NEUTRAL
                confidence REAL NOT NULL,
                agreement_count INTEGER NOT NULL,
                trigger_reason TEXT NOT NULL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                target_rrr REAL,
                agent_votes_json TEXT NOT NULL,
                features_snapshot_json TEXT NOT NULL,
                risk_status TEXT NOT NULL, -- APPROVED, VETOED
                risk_reason TEXT,
                executed INTEGER DEFAULT 0
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_decisions_sym ON decisions (symbol, timestamp DESC)")

            # 5. Executed Trade Journal & Post-Trade Outcome
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                ticket INTEGER PRIMARY KEY,
                decision_id INTEGER,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                volume REAL NOT NULL,
                entry_price REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                open_time TEXT NOT NULL,
                close_time TEXT,
                close_price REAL,
                profit REAL DEFAULT 0.0,
                realized_r REAL DEFAULT 0.0,
                slippage REAL DEFAULT 0.0,
                status TEXT NOT NULL, -- OPEN, CLOSED_TP, CLOSED_SL, CLOSED_BE, CLOSED_MANUAL, KILLED
                close_reason TEXT,
                FOREIGN KEY (decision_id) REFERENCES decisions (id)
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_sym ON trades (symbol, open_time DESC)")
            conn.commit()

    def store_candles(self, symbol: str, timeframe: str, candles: List[Dict[str, Any]]) -> int:
        """Stores a batch of OHLCV candles, replacing existing timestamps."""
        if not candles:
            return 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            records = [
                (
                    symbol,
                    timeframe,
                    int(c["time"]),
                    datetime.fromtimestamp(c["time"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    float(c["open"]),
                    float(c["high"]),
                    float(c["low"]),
                    float(c["close"]),
                    int(c.get("tick_volume", c.get("volume", 0))),
                    int(c.get("spread", 0))
                )
                for c in candles
            ]
            cursor.executemany("""
            INSERT OR REPLACE INTO candles (symbol, timeframe, timestamp, datetime_utc, open, high, low, close, tick_volume, spread)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, records)
            conn.commit()
            return len(records)

    def get_candles_df(self, symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
        """Retrieves candles as a pandas DataFrame sorted chronologically (oldest to newest)."""
        with self.get_connection() as conn:
            query = """
            SELECT timestamp, datetime_utc, open, high, low, close, tick_volume, spread
            FROM candles
            WHERE symbol = ? AND timeframe = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(symbol, timeframe, limit))
            if not df.empty:
                df = df.sort_values("timestamp").reset_index(drop=True)
            return df

    def record_decision(self, decision: Dict[str, Any]) -> int:
        """Logs a pre-trade decision with full specialist debate and features snapshot."""
        now = datetime.now(timezone.utc)
        ts = int(now.timestamp())
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO decisions (
                timestamp, datetime_utc, symbol, timeframe, consensus_bias,
                confidence, agreement_count, trigger_reason, entry_price,
                stop_loss, take_profit, target_rrr, agent_votes_json,
                features_snapshot_json, risk_status, risk_reason, executed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ts,
                now_str,
                decision.get("symbol", "UNKNOWN"),
                decision.get("timeframe", "M15"),
                decision.get("consensus_bias", "NEUTRAL"),
                float(decision.get("confidence", 0.0)),
                int(decision.get("agreement_count", 0)),
                decision.get("trigger_reason", ""),
                decision.get("entry_price"),
                decision.get("stop_loss"),
                decision.get("take_profit"),
                decision.get("target_rrr"),
                json.dumps(decision.get("agent_votes", {}), ensure_ascii=False),
                json.dumps(decision.get("features_snapshot", {}), ensure_ascii=False),
                decision.get("risk_status", "VETOED"),
                decision.get("risk_reason", ""),
                1 if decision.get("executed") else 0
            ))
            conn.commit()
            return cursor.lastrowid

    def record_trade_open(self, trade: Dict[str, Any]):
        """Logs newly opened trade execution from MT5."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO trades (
                ticket, decision_id, symbol, side, volume, entry_price,
                stop_loss, take_profit, open_time, status, slippage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(trade["ticket"]),
                trade.get("decision_id"),
                trade["symbol"],
                trade["side"],
                float(trade["volume"]),
                float(trade["entry_price"]),
                float(trade["stop_loss"]),
                float(trade["take_profit"]),
                trade.get("open_time", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
                "OPEN",
                float(trade.get("slippage", 0.0))
            ))
            conn.commit()

    def record_trade_close(self, ticket: int, close_price: float, profit: float, status: str, close_reason: str):
        """Updates trade outcome with realized profit and R-multiple."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Fetch entry & SL to compute realized R
            cursor.execute("SELECT side, entry_price, stop_loss FROM trades WHERE ticket = ?", (ticket,))
            row = cursor.fetchone()
            realized_r = 0.0
            if row and row["stop_loss"] and row["entry_price"]:
                risk_distance = abs(row["entry_price"] - row["stop_loss"])
                if risk_distance > 0:
                    gain = (close_price - row["entry_price"]) if row["side"] == "BUY" else (row["entry_price"] - close_price)
                    realized_r = round(gain / risk_distance, 2)

            cursor.execute("""
            UPDATE trades
            SET close_time = ?, close_price = ?, profit = ?, realized_r = ?, status = ?, close_reason = ?
            WHERE ticket = ?
            """, (now_str, float(close_price), float(profit), realized_r, status, close_reason, ticket))
            conn.commit()

    def backup_database(self) -> str:
        """Creates an automated daily backup of the SQLite database."""
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        backup_file = os.path.join(BACKUP_DIR, f"trading_desk_backup_{today}.db")
        shutil.copy2(self.db_path, backup_file)
        return backup_file

    def export_journal_csv(self, output_dir: Optional[str] = None) -> Dict[str, str]:
        """Exports trades and decisions to CSV on demand."""
        target_dir = output_dir or os.path.join(DB_DIR, "exports")
        os.makedirs(target_dir, exist_ok=True)
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        decisions_csv = os.path.join(target_dir, f"decisions_{now_str}.csv")
        trades_csv = os.path.join(target_dir, f"trades_{now_str}.csv")

        with self.get_connection() as conn:
            df_decisions = pd.read_sql_query("SELECT * FROM decisions ORDER BY timestamp DESC", conn)
            df_decisions.to_csv(decisions_csv, index=False)

            df_trades = pd.read_sql_query("SELECT * FROM trades ORDER BY open_time DESC", conn)
            df_trades.to_csv(trades_csv, index=False)

        return {"decisions_csv": decisions_csv, "trades_csv": trades_csv}
