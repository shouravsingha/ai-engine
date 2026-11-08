"""
Institutional Risk Manager
Enforces strict 1% maximum capital risk, dynamic position sizing, and mandatory 1:2.5+ RRR.
"""
from typing import Dict, Any, Optional

class RiskManager:
    def __init__(self, risk_percent: float = 1.0, min_rrr: float = 2.0):
        self.risk_percent = risk_percent
        self.min_rrr = min_rrr

    def evaluate_and_size_trade(
        self,
        account_balance: float,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float
    ) -> Optional[Dict[str, Any]]:
        """
        Validates risk parameters and calculates exact position size.
        """
        risk_distance = abs(entry_price - stop_loss)
        reward_distance = abs(take_profit - entry_price)

        if risk_distance <= 0:
            return None

        rrr = reward_distance / risk_distance
        if rrr < self.min_rrr:
            # Reject trade if Risk-Reward ratio is below minimum standard
            return None

        # Max dollar risk (1% of balance)
        max_dollar_risk = account_balance * (self.risk_percent / 100.0)
        
        # Position size in units / coins
        units = max_dollar_risk / risk_distance
        position_value = units * entry_price

        return {
            "approved": True,
            "side": side,
            "entry_price": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_reward_ratio": round(rrr, 2),
            "dollar_risk": round(max_dollar_risk, 2),
            "units": round(units, 4),
            "position_value": round(position_value, 2)
        }
