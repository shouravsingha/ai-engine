"""
Institutional Risk Manager & Capital Preservation Shield
Enforces strict dynamic capital risk, symbol contract sizing, hard dollar risk ceilings,
and account balance tier safeguards to eliminate margin wipeouts.
"""
from typing import Dict, Any, Optional

class RiskManager:
    def __init__(self, risk_percent: float = 1.0, min_rrr: float = 2.0, min_balance_threshold: float = 5.0):
        self.risk_percent = risk_percent
        self.min_rrr = min_rrr
        self.min_balance_threshold = min_balance_threshold
        
        # Standard contract sizes on Exness MT5
        # 1 lot Gold (XAUUSDm) = 100 troy oz ($1 move = $100 on 1 lot, $1 on 0.01 lot)
        # 1 lot BTCUSDm = 1 BTC ($100 move = $100 on 1 lot, $1 on 0.01 lot)
        # 1 lot ETHUSDm = 1 ETH ($10 move = $10 on 1 lot, $0.10 on 0.01 lot)
        # 1 lot Forex (EURUSDm, GBPUSDm, etc.) = 100,000 base currency units
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
        """
        Limits simultaneous open positions based on account equity.
        Prevents margin saturation and multi-pair liquidation.
        """
        return self.get_capital_tier(account_balance)["max_positions"]

    def get_contract_size(self, symbol: str) -> float:
        sym_upper = symbol.upper()
        # Metals / Crypto first
        if "XAU" in sym_upper or "GOLD" in sym_upper:
            return 100.0
        if "BTC" in sym_upper or "ETH" in sym_upper or "SOL" in sym_upper:
            return 1.0
        # Forex
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
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Validates trade risk against account capital, contract size, and broker minimums.
        Rejects trades that would over-risk capital at the minimum lot size.
        Supports both (entry_price, stop_loss, take_profit) and (entry, sl, tp) kwargs.
        """
        # 1. Guard against depleted or dangerously low balances
        if account_balance < self.min_balance_threshold:
            return None

        e_price = float(entry_price if entry_price is not None else kwargs.get("entry", 0.0))
        s_loss = float(stop_loss if stop_loss is not None else kwargs.get("sl", 0.0))
        t_profit = float(take_profit if take_profit is not None else kwargs.get("tp", 0.0))

        risk_distance = abs(e_price - s_loss)
        reward_distance = abs(t_profit - e_price)

        if risk_distance <= 0 or e_price <= 0:
            return None

        # 2. Risk-Reward Ratio Verification
        rrr = reward_distance / risk_distance
        if rrr < self.min_rrr:
            return None

        contract_size = self.get_contract_size(symbol)
        loss_per_one_lot = risk_distance * contract_size

        # 3. Dynamic Capital Allocation & Dollar Risk Ceilings
        tier = self.get_capital_tier(account_balance)
        max_dollar_risk = tier["max_dollar_risk"]
        max_volume_cap = tier["volume_cap"]

        # 4. Minimum Broker Volume (0.01 lot) Risk Check
        min_broker_lot = 0.01
        min_lot_loss = min_broker_lot * loss_per_one_lot

        # If 0.01 lot would lose more than allowable ceiling (with 25% tolerance), REJECT
        if min_lot_loss > (max_dollar_risk * 1.25):
            # For micro accounts, this specifically prevents taking wide Gold SL trades
            return None

        # 5. Position Sizing
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
