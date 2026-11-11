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
        self.contract_sizes = {
            "XAU": 100.0,
            "BTC": 1.0,
            "ETH": 1.0,
        }

    def get_max_allowed_positions(self, account_balance: float) -> int:
        """
        Limits simultaneous open positions based on account equity.
        Prevents margin saturation and multi-pair liquidation.
        """
        if account_balance < 50.0:
            return 1   # Micro accounts: strictly 1 single asset at a time
        elif account_balance < 250.0:
            return 1
        elif account_balance < 1000.0:
            return 2
        return 3

    def get_contract_size(self, symbol: str) -> float:
        sym_upper = symbol.upper()
        for k, v in self.contract_sizes.items():
            if k in sym_upper:
                return v
        return 1.0

    def evaluate_and_size_trade(
        self,
        account_balance: float,
        side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        symbol: str = "XAUUSDm"
    ) -> Optional[Dict[str, Any]]:
        """
        Validates trade risk against account capital, contract size, and broker minimums.
        Rejects trades that would over-risk capital at the minimum lot size.
        """
        # 1. Guard against depleted or dangerously low balances
        if account_balance < self.min_balance_threshold:
            return None

        risk_distance = abs(entry_price - stop_loss)
        reward_distance = abs(take_profit - entry_price)

        if risk_distance <= 0:
            return None

        # 2. Risk-Reward Ratio Verification
        rrr = reward_distance / risk_distance
        if rrr < self.min_rrr:
            return None

        contract_size = self.get_contract_size(symbol)
        loss_per_one_lot = risk_distance * contract_size

        # 3. Dynamic Capital Allocation & Dollar Risk Ceilings
        if account_balance < 50.0:
            # Micro Account Tier ($0-$50): Max 2.5% risk or $1.00 hard cap per trade
            max_dollar_risk = min(account_balance * 0.025, 1.00)
            max_volume_cap = 0.01
        elif account_balance < 200.0:
            # Small Account Tier ($50-$200): Max 2.0% risk or $3.00 cap
            max_dollar_risk = min(account_balance * 0.02, 3.00)
            max_volume_cap = 0.02
        elif account_balance < 1000.0:
            # Mid Tier ($200-$1000): Max 1.5% risk
            max_dollar_risk = account_balance * 0.015
            max_volume_cap = 0.05
        else:
            # Institutional Tier ($1000+): Strict 1.0% risk
            max_dollar_risk = account_balance * (self.risk_percent / 100.0)
            max_volume_cap = 1.00

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
        position_value = final_lot * contract_size * entry_price

        return {
            "approved": True,
            "symbol": symbol,
            "side": side,
            "entry_price": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_reward_ratio": round(rrr, 2),
            "dollar_risk": round(actual_dollar_risk, 2),
            "max_allowed_risk": round(max_dollar_risk, 2),
            "volume": round(final_lot, 2),
            "units": round(final_lot, 2),
            "contract_size": contract_size,
            "position_value": round(position_value, 2)
        }
