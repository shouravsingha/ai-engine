"""
Institutional Demo / Paper Trading Account
Initial capital: $50,000.00 USD
Tracks active orders, closed trades, Win-rate, and equity growth curve.
"""
from datetime import datetime
from typing import Dict, Any, List

class DemoAccount:
    def __init__(self, initial_capital: float = 50000.0):
        self.initial_capital = initial_capital
        self.balance = initial_capital
        self.equity = initial_capital
        self.open_trades: List[Dict[str, Any]] = []
        self.trade_history: List[Dict[str, Any]] = []
        self.winning_trades = 0
        self.total_closed = 0

    def open_trade(self, trade_plan: Dict[str, Any], symbol: str = "BTCUSDT") -> Dict[str, Any]:
        trade_id = f"TRADE-{len(self.trade_history) + len(self.open_trades) + 1:04d}"
        trade = {
            "id": trade_id,
            "symbol": symbol,
            "side": trade_plan["side"],
            "entry_price": trade_plan["entry_price"],
            "stop_loss": trade_plan["stop_loss"],
            "take_profit": trade_plan["take_profit"],
            "units": trade_plan["units"],
            "risk_dollar": trade_plan["dollar_risk"],
            "rrr": trade_plan["risk_reward_ratio"],
            "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_pnl": 0.0,
            "status": "OPEN"
        }
        self.open_trades.append(trade)
        return trade

    def update_open_trades(self, current_price: float) -> List[Dict[str, Any]]:
        """Checks for Stop-Loss or Take-Profit hits and updates unrealized PnL."""
        closed_this_round = []
        remaining_trades = []

        unrealized = 0.0
        for trade in self.open_trades:
            side = trade["side"]
            entry = trade["entry_price"]
            sl = trade["stop_loss"]
            tp = trade["take_profit"]
            units = trade["units"]

            # Calculate floating PnL
            if side == "BUY":
                pnl = (current_price - entry) * units
                # Check hit TP or SL
                if current_price >= tp:
                    trade["status"] = "CLOSED_WIN (TP HIT)"
                    trade["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trade["realized_pnl"] = (tp - entry) * units
                    self.balance += trade["realized_pnl"]
                    self.winning_trades += 1
                    self.total_closed += 1
                    self.trade_history.append(trade)
                    closed_this_round.append(trade)
                    continue
                elif current_price <= sl:
                    trade["status"] = "CLOSED_LOSS (SL HIT)"
                    trade["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trade["realized_pnl"] = (sl - entry) * units
                    self.balance += trade["realized_pnl"]
                    self.total_closed += 1
                    self.trade_history.append(trade)
                    closed_this_round.append(trade)
                    continue
            else:
                pnl = (entry - current_price) * units
                if current_price <= tp:
                    trade["status"] = "CLOSED_WIN (TP HIT)"
                    trade["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trade["realized_pnl"] = (entry - tp) * units
                    self.balance += trade["realized_pnl"]
                    self.winning_trades += 1
                    self.total_closed += 1
                    self.trade_history.append(trade)
                    closed_this_round.append(trade)
                    continue
                elif current_price >= sl:
                    trade["status"] = "CLOSED_LOSS (SL HIT)"
                    trade["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trade["realized_pnl"] = (entry - sl) * units
                    self.balance += trade["realized_pnl"]
                    self.total_closed += 1
                    self.trade_history.append(trade)
                    closed_this_round.append(trade)
                    continue

            trade["current_pnl"] = round(pnl, 2)
            unrealized += pnl
            remaining_trades.append(trade)

        self.open_trades = remaining_trades
        self.equity = round(self.balance + unrealized, 2)
        return closed_this_round

    def get_summary(self) -> Dict[str, Any]:
        win_rate = (self.winning_trades / self.total_closed * 100) if self.total_closed > 0 else 0.0
        return {
            "initial_capital": self.initial_capital,
            "balance": round(self.balance, 2),
            "equity": self.equity,
            "total_pnl": round(self.equity - self.initial_capital, 2),
            "pnl_percent": round(((self.equity - self.initial_capital) / self.initial_capital) * 100, 2),
            "win_rate": round(win_rate, 1),
            "open_trades_count": len(self.open_trades),
            "closed_trades_count": self.total_closed
        }
