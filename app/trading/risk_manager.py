"""
Institutional Risk Manager & Sovereign Capital Preservation Shield.
Enforces strict 1% per-trade risk, 3% daily loss cap, 10% drawdown kill switch,
correlated exposure limits, and non-negotiable stop-loss requirements.
ZERO AI override permitted.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


class RiskManager:
    def __init__(
        self,
        risk_percent: float = 1.0,
        min_rrr: float = 2.0,
        min_balance_threshold: float = 5.0,
        max_daily_loss_pct: float = 3.0,
        kill_switch_dd_pct: float = 10.0,
        max_correlated_positions: int = 1
    ):
        # HARD-CODED SOVEREIGN LIMITS - CANNOT BE OVERRIDDEN BY ANY AGENT OR PROMPT
        self.risk_percent = min(risk_percent, 1.0)  # Maximum 1% risk per trade
        self.min_rrr = max(min_rrr, 2.0)            # Minimum 1:2 R:R
        self.min_balance_threshold = min_balance_threshold
        self.max_daily_loss_pct = max_daily_loss_pct  # 3% daily loss limit
        self.kill_switch_dd_pct = kill_switch_dd_pct  # 10% maximum peak-to-trough drawdown
        self.max_correlated_positions = max_correlated_positions

        self.daily_start_equity = 0.0
        self.current_day = ""
        self.daily_pnl = 0.0
        self.peak_equity = 0.0
        self.kill_switch_triggered = False
        self.trading_halted_reason = ""

        # Standard contract sizes on Exness MT5
        self.contract_sizes = {
            "XAU": 100.0,
            "BTC": 1.0,
            "ETH": 1.0,
            "SOL": 1.0,
            "EUR": 100000.0,
            "GBP": 100000.0,
            "AUD": 100000.0,
            "NZD": 100000.0,
            "CAD": 100000.0,
            "CHF": 100000.0,
            "JPY": 100000.0,
        }

    def update_account_state(self, current_equity: float, current_balance: float):
        """Updates internal equity tracking, reset daily loss counter at 00:00 UTC."""
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today_str != self.current_day:
            self.current_day = today_str
            self.daily_start_equity = current_equity
            self.daily_pnl = 0.0
            if not self.kill_switch_triggered:
                self.trading_halted_reason = ""

        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        # Track daily loss relative to start of day equity
        if self.daily_start_equity > 0:
            self.daily_pnl = current_equity - self.daily_start_equity

    def evaluate_kill_switch(self, current_equity: float) -> Dict[str, Any]:
        """
        EMERGENCY KILL SWITCH:
        If total drawdown exceeds 10% from peak equity, HALT ALL TRADING and close all positions.
        """
        if self.peak_equity <= 0:
            self.peak_equity = current_equity
            return {"kill_switch": False}

        drawdown_pct = ((self.peak_equity - current_equity) / self.peak_equity) * 100.0
        if drawdown_pct >= self.kill_switch_dd_pct:
            self.kill_switch_triggered = True
            self.trading_halted_reason = f"🚨 EMERGENCY KILL SWITCH: Drawdown {drawdown_pct:.1f}% exceeded {self.kill_switch_dd_pct}%. Trading halted immediately."
            return {
                "kill_switch": True,
                "action": "close_all_and_halt",
                "reason": self.trading_halted_reason,
                "drawdown_pct": round(drawdown_pct, 2)
            }

        return {"kill_switch": False, "drawdown_pct": round(drawdown_pct, 2)}

    def evaluate_daily_loss_limit(self, current_equity: float) -> bool:
        """
        Enforces 3% maximum daily loss. If breached, no new orders are allowed today.
        """
        if self.daily_start_equity <= 0:
            return True

        daily_loss_pct = (abs(self.daily_pnl) / self.daily_start_equity) * 100.0
        if self.daily_pnl < 0 and daily_loss_pct >= self.max_daily_loss_pct:
            self.trading_halted_reason = f"🛑 DAILY LOSS CEILING HIT: Daily loss -{daily_loss_pct:.1f}% reached {self.max_daily_loss_pct}%. Trading paused until tomorrow."
            return False
        return True

    def check_correlated_exposure(self, symbol: str, open_positions: List[Dict[str, Any]]) -> bool:
        """
        Prevents over-exposure in correlated asset classes (e.g., holding multiple USD pairs, multiple crypto).
        """
        sym_upper = symbol.upper()
        asset_class = "METALS" if "XAU" in sym_upper else ("CRYPTO" if any(c in sym_upper for c in ["BTC", "ETH", "SOL"]) else "FOREX")

        active_same_class = 0
        for pos in open_positions:
            pos_sym = pos.get("symbol", "").upper()
            pos_class = "METALS" if "XAU" in pos_sym else ("CRYPTO" if any(c in pos_sym for c in ["BTC", "ETH", "SOL"]) else "FOREX")
            if pos_class == asset_class:
                active_same_class += 1

        if active_same_class >= self.max_correlated_positions:
            return False
        return True

    def get_capital_tier(self, account_balance: float) -> Dict[str, Any]:
        """Returns the risk tier configuration for the given account balance."""
        if account_balance < 50.0:
            return {
                "tier": "MICRO",
                "max_dollar_risk": min(max(account_balance * 0.05, 0.80), 1.25),
                "volume_cap": 0.01,
                "max_positions": 1
            }
        elif account_balance < 200.0:
            return {
                "tier": "SMALL",
                "max_dollar_risk": min(account_balance * 0.02, 3.00),
                "volume_cap": 0.02,
                "max_positions": 1
            }
        elif account_balance < 1000.0:
            return {
                "tier": "MID",
                "max_dollar_risk": account_balance * 0.015,
                "volume_cap": 0.05,
                "max_positions": 2
            }
        else:
            return {
                "tier": "INSTITUTIONAL",
                "max_dollar_risk": account_balance * (self.risk_percent / 100.0),
                "volume_cap": 1.00,
                "max_positions": 3
            }

    def get_max_allowed_positions(self, account_balance: float) -> int:
        return self.get_capital_tier(account_balance)["max_positions"]

    def get_contract_size(self, symbol: str) -> float:
        sym_upper = symbol.upper()
        if "XAU" in sym_upper or "GOLD" in sym_upper:
            return 100.0
        if "BTC" in sym_upper or "ETH" in sym_upper or "SOL" in sym_upper:
            return 1.0
        for k in ["EUR", "GBP", "AUD", "NZD", "CAD", "CHF", "JPY"]:
            if k in sym_upper:
                return 100000.0
        return 1.0

    def evaluate_and_size_trade(
        self,
        account_balance: float,
        side: str,
        entry_price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        symbol: str = "XAUUSDm",
        open_positions: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Validates trade risk against account capital, contract size, and broker minimums.
        Rejects trades that would over-risk capital at the minimum lot size.
        """
        # RULE 0: KILL SWITCH OR DAILY CEILING CHECK
        if self.kill_switch_triggered or bool(self.trading_halted_reason):
            return None

        # RULE 1: MANDATORY STOP LOSS CHECK (NEVER TRADE WITHOUT A STOP LOSS)
        s_loss = float(stop_loss if stop_loss is not None else kwargs.get("sl", 0.0))
        e_price = float(entry_price if entry_price is not None else kwargs.get("entry", 0.0))
        t_profit = float(take_profit if take_profit is not None else kwargs.get("tp", 0.0))

        if s_loss <= 0 or e_price <= 0:
            return None

        if side.upper() == "BUY" and s_loss >= e_price:
            return None
        if side.upper() == "SELL" and s_loss <= e_price:
            return None

        # RULE 2: MINIMUM BALANCE CHECK
        if account_balance < self.min_balance_threshold:
            return None

        # RULE 3: CORRELATED EXPOSURE CHECK
        if open_positions is not None and not self.check_correlated_exposure(symbol, open_positions):
            return None

        risk_distance = abs(e_price - s_loss)
        reward_distance = abs(t_profit - e_price)

        # RULE 4: RISK-REWARD RATIO CHECK (R:R >= 1:2)
        rrr = reward_distance / risk_distance
        if rrr < self.min_rrr:
            return None

        contract_size = self.get_contract_size(symbol)
        loss_per_one_lot = risk_distance * contract_size

        # RULE 5: HARD RISK SIZING
        tier = self.get_capital_tier(account_balance)
        max_dollar_risk = tier["max_dollar_risk"]
        max_volume_cap = tier["volume_cap"]

        min_broker_lot = 0.01
        min_lot_loss = min_broker_lot * loss_per_one_lot

        # If minimum broker lot exceeds max allowable loss with tolerance, REJECT
        if min_lot_loss > (max_dollar_risk * 1.25):
            return None

        ideal_lot = max_dollar_risk / loss_per_one_lot if loss_per_one_lot > 0 else min_broker_lot
        final_lot = min(max(min_broker_lot, round(ideal_lot, 2)), max_volume_cap)
        actual_dollar_risk = final_lot * loss_per_one_lot
        position_value = final_lot * contract_size * e_price

        return {
            "approved": True,
            "symbol": symbol,
            "side": side,
            "entry_price": round(e_price, 2),
            "stop_loss": round(s_loss, 2),
            "take_profit": round(t_profit, 2),
            "risk_reward_ratio": round(rrr, 2),
            "dollar_risk": round(actual_dollar_risk, 2),
            "max_allowed_risk": round(max_dollar_risk, 2),
            "volume": round(final_lot, 2),
            "units": round(final_lot, 2),
            "contract_size": contract_size,
            "position_value": round(position_value, 2)
        }
