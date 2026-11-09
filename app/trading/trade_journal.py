"""
Trade Journal & Persistent Trade History Database (SQLite)
Saves every opened and closed MT5 position permanently.
Computes Win-rate, Total Realized PnL, Daily PnL, and AI post-mortem notes.
"""
import os
import sqlite3
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "trades.db")

class TradeJournal:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    volume REAL NOT NULL,
                    open_price REAL NOT NULL,
                    close_price REAL DEFAULT 0.0,
                    sl REAL DEFAULT 0.0,
                    tp REAL DEFAULT 0.0,
                    profit REAL DEFAULT 0.0,
                    open_time TEXT NOT NULL,
                    close_time TEXT DEFAULT '',
                    status TEXT DEFAULT 'OPEN',
                    exit_reason TEXT DEFAULT '',
                    ai_notes TEXT DEFAULT ''
                )
            """)
            conn.commit()

    def record_open_trade(self, ticket: Any, symbol: str, side: str, volume: float, 
                          open_price: float, sl: float = 0.0, tp: float = 0.0, ai_notes: str = "") -> bool:
        """Records a new open trade or updates if already exists."""
        ticket_str = str(ticket)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO trades (ticket, symbol, side, volume, open_price, sl, tp, open_time, status, ai_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
                    ON CONFLICT(ticket) DO UPDATE SET
                        sl = excluded.sl,
                        tp = excluded.tp,
                        ai_notes = excluded.ai_notes
                """, (ticket_str, symbol, side.upper(), float(volume), float(open_price), float(sl), float(tp), now_str, ai_notes))
                conn.commit()
                return True
        except Exception as e:
            print(f"[JOURNAL ERROR] Open trade record error: {e}")
            return False

    def record_closed_trade(self, ticket: Any, close_price: float, profit: float, 
                            exit_reason: str = "TP/SL Settlement", close_time: str = "") -> bool:
        """Marks a trade as closed and records realized PnL."""
        ticket_str = str(ticket)
        if not close_time:
            close_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "WIN" if profit > 0 else ("BREAKEVEN" if profit == 0 else "LOSS")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE trades 
                    SET close_price = ?, profit = ?, close_time = ?, status = ?, exit_reason = ?
                    WHERE ticket = ?
                """, (float(close_price), float(profit), close_time, status, exit_reason, ticket_str))
                conn.commit()
                return True
        except Exception as e:
            print(f"[JOURNAL ERROR] Close trade record error: {e}")
            return False

    def sync_mt5_history(self, exness_bridge) -> int:
        """
        Pulls actual closed deals from local MT5 and populates SQLite database.
        """
        try:
            import MetaTrader5 as mt5
            if not (mt5.initialize() and exness_bridge.live_terminal):
                return 0

            # Pull deals for past 30 days
            from_date = datetime.now().timestamp() - (30 * 86400)
            to_date = datetime.now().timestamp() + 86400
            deals = mt5.history_deals_get(from_date, to_date)
            
            if not deals:
                return 0

            synced_count = 0
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for d in deals:
                    # Entry OUT (closing deal) has profit != 0 or entry == 1
                    if getattr(d, 'entry', -1) == 1 and d.position_id > 0:
                        t_ticket = str(d.position_id)
                        t_sym = d.symbol
                        t_profit = round(float(d.profit + d.swap + d.commission), 2)
                        t_price = float(d.price)
                        t_time = datetime.fromtimestamp(d.time).strftime("%Y-%m-%d %H:%M:%S")
                        t_vol = float(d.volume)
                        t_status = "WIN" if t_profit > 0 else ("BREAKEVEN" if t_profit == 0 else "LOSS")
                        t_comment = d.comment or "MT5 Execution"

                        cursor.execute("""
                            INSERT INTO trades (ticket, symbol, side, volume, open_price, close_price, profit, open_time, close_time, status, exit_reason)
                            VALUES (?, ?, 'DEAL', ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(ticket) DO UPDATE SET
                                close_price = excluded.close_price,
                                profit = excluded.profit,
                                close_time = excluded.close_time,
                                status = excluded.status,
                                exit_reason = excluded.exit_reason
                        """, (t_ticket, t_sym, t_vol, t_price, t_price, t_profit, t_time, t_time, t_status, t_comment))
                        synced_count += 1
                conn.commit()
            return synced_count
        except Exception as e:
            return 0

    def get_recent_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns list of recent trades for dashboard table."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ticket, symbol, side, volume, open_price, close_price, sl, tp, profit, open_time, close_time, status, exit_reason, ai_notes
                    FROM trades
                    ORDER BY id DESC
                    LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            print(f"[JOURNAL ERROR] Query recent trades error: {e}")
            return []

    def get_account_stats(self) -> Dict[str, Any]:
        """Calculates win rate, total PnL, today PnL, and breakdown."""
        try:
            today_prefix = date.today().strftime("%Y-%m-%d")
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT status, profit, close_time FROM trades WHERE status IN ('WIN', 'LOSS', 'BREAKEVEN')")
                rows = cursor.fetchall()

                total_closed = len(rows)
                wins = sum(1 for r in rows if r["status"] == "WIN")
                losses = sum(1 for r in rows if r["status"] == "LOSS")
                total_pnl = sum(r["profit"] for r in rows)
                today_pnl = sum(r["profit"] for r in rows if r["close_time"] and r["close_time"].startswith(today_prefix))

                win_rate = round((wins / total_closed * 100), 1) if total_closed > 0 else 0.0

                return {
                    "total_trades": total_closed,
                    "wins": wins,
                    "losses": losses,
                    "win_rate": win_rate,
                    "total_realized_pnl": round(total_pnl, 2),
                    "today_pnl": round(today_pnl, 2)
                }
        except Exception as e:
            return {
                "total_trades": 0, "wins": 0, "losses": 0,
                "win_rate": 0.0, "total_realized_pnl": 0.0, "today_pnl": 0.0
            }
