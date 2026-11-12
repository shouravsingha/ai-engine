"""
Trade Journal & Statistical Learning Engine for Human-Like Trading Desk.
Maintains continuous audit trail of all pre-trade decisions, specialist debates,
features snapshots, post-trade outcomes, and computes statistical edge.
"""

import json
import math
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.data.db_manager import DatabaseManager


class TradeJournal:
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    def log_decision_event(
        self,
        symbol: str,
        timeframe: str,
        consensus_bias: str,
        confidence: float,
        agreement_count: int,
        trigger_reason: str,
        entry_price: Optional[float],
        stop_loss: Optional[float],
        take_profit: Optional[float],
        agent_votes: Dict[str, Any],
        features_snapshot: Dict[str, Any],
        risk_status: str,
        risk_reason: str = "",
        executed: bool = False
    ) -> int:
        """
        Logs complete decision audit into SQLite database before trade placement.
        """
        target_rrr = 0.0
        if entry_price and stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            if risk > 0:
                target_rrr = round(reward / risk, 2)

        decision_data = {
            "symbol": symbol,
            "timeframe": timeframe,
            "consensus_bias": consensus_bias,
            "confidence": confidence,
            "agreement_count": agreement_count,
            "trigger_reason": trigger_reason,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "target_rrr": target_rrr,
            "agent_votes": agent_votes,
            "features_snapshot": features_snapshot,
            "risk_status": risk_status,
            "risk_reason": risk_reason,
            "executed": executed
        }
        return self.db.record_decision(decision_data)

    def log_trade_execution(
        self,
        ticket: int,
        decision_id: Optional[int],
        symbol: str,
        side: str,
        volume: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        slippage: float = 0.0
    ):
        """Records initial trade fill from MT5."""
        trade_record = {
            "ticket": ticket,
            "decision_id": decision_id,
            "symbol": symbol,
            "side": side,
            "volume": volume,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "slippage": slippage,
            "open_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        }
        self.db.record_trade_open(trade_record)

    def log_trade_outcome(
        self,
        ticket: int,
        close_price: float,
        profit: float,
        status: str,
        close_reason: str
    ):
        """Records trade closure and calculates realized R-multiple."""
        self.db.record_trade_close(ticket, close_price, profit, status, close_reason)

    def get_recent_decisions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieves recent decisions formatted for dashboard viewing."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT id, datetime_utc, symbol, timeframe, consensus_bias,
                   confidence, agreement_count, trigger_reason, entry_price,
                   stop_loss, take_profit, target_rrr, agent_votes_json,
                   risk_status, risk_reason, executed
            FROM decisions
            ORDER BY timestamp DESC
            LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["agent_votes"] = json.loads(item.pop("agent_votes_json"))
                results.append(item)
            return results

    def analyze_statistical_edge(self, min_sample_size: int = 30) -> Dict[str, Any]:
        """
        Analyzes edge across recorded trades:
        - Filters out setup types with fewer than 30 samples
        - Performs statistical significance check (Z-test / t-test approximation)
        - Computes win rate, avg R, profit factor, and max drawdown.
        """
        with self.db.get_connection() as conn:
            query = """
            SELECT t.ticket, t.symbol, t.side, t.volume, t.entry_price, t.close_price,
                   t.profit, t.realized_r, t.status, d.trigger_reason, d.timeframe,
                   t.open_time, t.close_time
            FROM trades t
            LEFT JOIN decisions d ON t.decision_id = d.id
            WHERE t.status != 'OPEN' AND t.close_time IS NOT NULL
            """
            df = pd.read_sql_query(query, conn)

        if df.empty or len(df) == 0:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_r": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "statistically_validated_setups": [],
                "unvalidated_setups": [],
                "note": "Insufficient historical trade sample. Requires >= 30 closed trades."
            }

        total_trades = len(df)
        wins = df[df["profit"] > 0]
        losses = df[df["profit"] <= 0]
        win_rate = round((len(wins) / total_trades) * 100, 2)
        avg_r = round(float(df["realized_r"].mean()), 2)

        gross_profit = float(wins["profit"].sum()) if not wins.empty else 0.0
        gross_loss = abs(float(losses["profit"].sum())) if not losses.empty else 0.0001
        profit_factor = round(gross_profit / gross_loss, 2)

        # Drawdown calculation
        cumulative_pnl = df["profit"].cumsum()
        running_peak = cumulative_pnl.cummax()
        drawdown = running_peak - cumulative_pnl
        max_drawdown = round(float(drawdown.max()), 2)

        # Group by setup type / trigger reason
        setup_groups = df.groupby("trigger_reason")
        validated_setups = []
        unvalidated_setups = []

        for setup, group in setup_groups:
            n = len(group)
            setup_wins = len(group[group["profit"] > 0])
            setup_win_rate = (setup_wins / n) * 100
            setup_avg_r = float(group["realized_r"].mean())

            # Edge Significance Check (Standard Error of proportion)
            # Edge exists if Win Rate > 50% with p < 0.05 on N >= 30
            p_hat = setup_wins / n
            se = math.sqrt((0.5 * 0.5) / n) if n > 0 else 1.0
            z_score = (p_hat - 0.5) / se if se > 0 else 0.0

            setup_data = {
                "setup": setup or "Discretionary / Unclassified",
                "sample_size": n,
                "win_rate": round(setup_win_rate, 2),
                "avg_r": round(setup_avg_r, 2),
                "profit_factor": round(float(group[group["profit"] > 0]["profit"].sum()) / max(abs(float(group[group["profit"] <= 0]["profit"].sum())), 0.01), 2),
                "z_score": round(z_score, 2),
                "has_stat_edge": (n >= min_sample_size and z_score > 1.645 and setup_avg_r > 0.3)
            }

            if setup_data["has_stat_edge"]:
                validated_setups.append(setup_data)
            else:
                unvalidated_setups.append(setup_data)

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_r": avg_r,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "statistically_validated_setups": validated_setups,
            "unvalidated_setups": unvalidated_setups
        }

    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generates institutional weekly trade performance audit report."""
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            query = """
            SELECT t.ticket, t.symbol, t.side, t.volume, t.entry_price, t.close_price,
                   t.profit, t.realized_r, t.status, d.trigger_reason, d.timeframe,
                   t.open_time, t.close_time
            FROM trades t
            LEFT JOIN decisions d ON t.decision_id = d.id
            WHERE t.close_time >= ?
            """
            df_week = pd.read_sql_query(query, conn, params=(seven_days_ago,))

        if df_week.empty:
            return {
                "period": "Last 7 Days",
                "total_trades": 0,
                "net_profit": 0.0,
                "win_rate": 0.0,
                "status": "No trades executed in the last 7 days."
            }

        total = len(df_week)
        wins = df_week[df_week["profit"] > 0]
        net_profit = round(float(df_week["profit"].sum()), 2)
        win_rate = round((len(wins) / total) * 100, 2)
        avg_r = round(float(df_week["realized_r"].mean()), 2)

        by_symbol = df_week.groupby("symbol")["profit"].sum().round(2).to_dict()

        return {
            "period": "Last 7 Days",
            "total_trades": total,
            "net_profit": net_profit,
            "win_rate": win_rate,
            "avg_r": avg_r,
            "by_symbol": by_symbol,
            "trades": df_week[["ticket", "symbol", "side", "profit", "realized_r", "close_time"]].to_dict(orient="records")
        }
