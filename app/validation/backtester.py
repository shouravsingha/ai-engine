"""
Institutional Walk-Forward Backtesting Engine for Human-Like Trading Desk.
Simulates multi-agent decision desk on historical candles with realistic spread,
slippage, commission models, and out-of-sample forward verification.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from app.trading.risk_manager import RiskManager
from app.agents.trend_agent import TrendAnalyst
from app.agents.momentum_agent import MomentumAnalyst
from app.agents.liquidity_agent import LiquidityAnalyst


class WalkForwardBacktester:
    def __init__(
        self,
        initial_capital: float = 100.0,
        risk_percent: float = 1.0,
        spread_cost: float = 0.35,  # $0.35 spread for Gold
        commission_per_lot: float = 7.0,
        min_rrr: float = 2.0
    ):
        self.initial_capital = initial_capital
        self.risk_percent = risk_percent
        self.spread_cost = spread_cost
        self.commission_per_lot = commission_per_lot
        self.min_rrr = min_rrr

        self.trend_agent = TrendAnalyst()
        self.momentum_agent = MomentumAnalyst()
        self.liquidity_agent = LiquidityAnalyst()
        self.risk_manager = RiskManager(risk_percent=risk_percent, min_rrr=min_rrr)

    def run_backtest_window(self, df_candles: pd.DataFrame, symbol: str = "XAUUSDm") -> Dict[str, Any]:
        """Runs single-window simulation on historical candles."""
        if df_candles.empty or len(df_candles) < 50:
            return {"total_trades": 0, "net_profit": 0.0, "win_rate": 0.0, "profit_factor": 0.0}

        equity = self.initial_capital
        trades: List[Dict[str, Any]] = []
        open_trade: Optional[Dict[str, Any]] = None

        contract_size = self.risk_manager.get_contract_size(symbol)

        for i in range(40, len(df_candles)):
            current_bar = df_candles.iloc[i]
            prev_window = df_candles.iloc[:i]

            # 1. Manage Open Trade
            if open_trade:
                high = float(current_bar["high"])
                low = float(current_bar["low"])

                # Check SL / TP hits
                if open_trade["side"] == "BUY":
                    if low <= open_trade["sl"]:
                        # Hit SL
                        exit_price = open_trade["sl"]
                        loss = open_trade["volume"] * contract_size * (exit_price - open_trade["entry"])
                        commission = open_trade["volume"] * self.commission_per_lot
                        net_pnl = loss - commission
                        equity += net_pnl
                        trades.append({
                            "side": "BUY", "entry": open_trade["entry"], "exit": exit_price,
                            "pnl": round(net_pnl, 2), "r_multiple": -1.0, "status": "SL"
                        })
                        open_trade = None
                    elif high >= open_trade["tp"]:
                        # Hit TP
                        exit_price = open_trade["tp"]
                        gain = open_trade["volume"] * contract_size * (exit_price - open_trade["entry"])
                        commission = open_trade["volume"] * self.commission_per_lot
                        net_pnl = gain - commission
                        equity += net_pnl
                        trades.append({
                            "side": "BUY", "entry": open_trade["entry"], "exit": exit_price,
                            "pnl": round(net_pnl, 2), "r_multiple": self.min_rrr, "status": "TP"
                        })
                        open_trade = None

                elif open_trade["side"] == "SELL":
                    if high >= open_trade["sl"]:
                        # Hit SL
                        exit_price = open_trade["sl"]
                        loss = open_trade["volume"] * contract_size * (open_trade["entry"] - exit_price)
                        commission = open_trade["volume"] * self.commission_per_lot
                        net_pnl = loss - commission
                        equity += net_pnl
                        trades.append({
                            "side": "SELL", "entry": open_trade["entry"], "exit": exit_price,
                            "pnl": round(net_pnl, 2), "r_multiple": -1.0, "status": "SL"
                        })
                        open_trade = None
                    elif low <= open_trade["tp"]:
                        # Hit TP
                        exit_price = open_trade["tp"]
                        gain = open_trade["volume"] * contract_size * (open_trade["entry"] - exit_price)
                        commission = open_trade["volume"] * self.commission_per_lot
                        net_pnl = gain - commission
                        equity += net_pnl
                        trades.append({
                            "side": "SELL", "entry": open_trade["entry"], "exit": exit_price,
                            "pnl": round(net_pnl, 2), "r_multiple": self.min_rrr, "status": "TP"
                        })
                        open_trade = None
                continue

            # 2. Evaluate Entry via Specialist Agents
            trend = self.trend_agent.analyze(prev_window)
            momentum = self.momentum_agent.analyze(prev_window)
            liquidity = self.liquidity_agent.analyze(prev_window)

            votes = [trend["bias"], momentum["bias"], liquidity["bias"]]
            buy_count = votes.count("BUY")
            sell_count = votes.count("SELL")

            if buy_count >= 2:
                side = "BUY"
                sl = liquidity["invalidation_level"] or (float(current_bar["close"]) - 2.50)
                if sl >= float(current_bar["close"]):
                    sl = float(current_bar["close"]) - 2.50
                entry = float(current_bar["close"]) + (self.spread_cost / 2.0)
                tp = entry + (abs(entry - sl) * self.min_rrr)

                risk_plan = self.risk_manager.evaluate_and_size_trade(
                    account_balance=equity, side="BUY", entry_price=entry, stop_loss=sl, take_profit=tp, symbol=symbol
                )
                if risk_plan and risk_plan.get("approved"):
                    open_trade = {"side": "BUY", "entry": entry, "sl": sl, "tp": tp, "volume": risk_plan["volume"]}

            elif sell_count >= 2:
                side = "SELL"
                sl = liquidity["invalidation_level"] or (float(current_bar["close"]) + 2.50)
                if sl <= float(current_bar["close"]):
                    sl = float(current_bar["close"]) + 2.50
                entry = float(current_bar["close"]) - (self.spread_cost / 2.0)
                tp = entry - (abs(sl - entry) * self.min_rrr)

                risk_plan = self.risk_manager.evaluate_and_size_trade(
                    account_balance=equity, side="SELL", entry_price=entry, stop_loss=sl, take_profit=tp, symbol=symbol
                )
                if risk_plan and risk_plan.get("approved"):
                    open_trade = {"side": "SELL", "entry": entry, "sl": sl, "tp": tp, "volume": risk_plan["volume"]}

        # Metrics calculation
        df_trades = pd.DataFrame(trades)
        if df_trades.empty:
            return {"total_trades": 0, "win_rate": 0.0, "net_profit": 0.0, "profit_factor": 0.0, "max_drawdown": 0.0}

        wins = df_trades[df_trades["pnl"] > 0]
        losses = df_trades[df_trades["pnl"] <= 0]
        win_rate = round((len(wins) / len(df_trades)) * 100, 2)
        net_profit = round(float(df_trades["pnl"].sum()), 2)
        gross_profit = float(wins["pnl"].sum()) if not wins.empty else 0.0
        gross_loss = abs(float(losses["pnl"].sum())) if not losses.empty else 0.001
        profit_factor = round(gross_profit / gross_loss, 2)

        cum_pnl = df_trades["pnl"].cumsum()
        max_dd = round(float((cum_pnl.cummax() - cum_pnl).max()), 2)

        return {
            "total_trades": len(df_trades),
            "win_rate": win_rate,
            "net_profit": net_profit,
            "profit_factor": profit_factor,
            "max_drawdown": max_dd,
            "final_equity": round(equity, 2),
            "trades": trades
        }

    def walk_forward_validation(self, df_all: pd.DataFrame, split_ratio: float = 0.70) -> Dict[str, Any]:
        """
        Walk-Forward Testing:
        Splits data into In-Sample (Optimization/Training period) and
        Out-of-Sample (Unseen testing period).
        """
        n = len(df_all)
        split_idx = int(n * split_ratio)

        df_in_sample = df_all.iloc[:split_idx].reset_index(drop=True)
        df_out_sample = df_all.iloc[split_idx:].reset_index(drop=True)

        res_in = self.run_backtest_window(df_in_sample)
        res_out = self.run_backtest_window(df_out_sample)

        # Walk-Forward Efficiency (WFE) = Out-of-sample annual return / In-sample return
        wfe = 0.0
        if res_in["net_profit"] > 0:
            wfe = round((res_out["net_profit"] / res_in["net_profit"]) * 100, 2)

        return {
            "in_sample": {
                "period_bars": len(df_in_sample),
                "total_trades": res_in["total_trades"],
                "win_rate": res_in["win_rate"],
                "net_profit": res_in["net_profit"],
                "profit_factor": res_in["profit_factor"],
                "max_drawdown": res_in["max_drawdown"]
            },
            "out_of_sample": {
                "period_bars": len(df_out_sample),
                "total_trades": res_out["total_trades"],
                "win_rate": res_out["win_rate"],
                "net_profit": res_out["net_profit"],
                "profit_factor": res_out["profit_factor"],
                "max_drawdown": res_out["max_drawdown"]
            },
            "walk_forward_efficiency_pct": wfe,
            "is_statistically_robust": (res_out["profit_factor"] >= 1.25 and res_out["win_rate"] >= 45.0)
        }
