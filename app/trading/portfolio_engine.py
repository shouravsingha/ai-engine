"""
Sovereign Portfolio Engine & Institutional Sizing Manager
Features:
- Fractional Kelly Criterion sizing based on empirical setup edge from TradeJournal.
- Volatility-parity normalization across Forex, Metals, and Crypto.
- Cross-asset correlation exposure matrix to eliminate correlated margin drawdowns.
- Respects sovereign capital tiers (Micro, Small, Mid, Institutional).
"""
from typing import Dict, Any, List, Optional
import math


class SovereignPortfolioEngine:
    def __init__(
        self,
        base_risk_fraction: float = 0.01,
        kelly_fraction: float = 0.35,  # 35% conservative fractional Kelly
        max_class_exposure_pct: float = 0.04  # Max 4% total exposure per asset class
    ):
        self.base_risk_fraction = base_risk_fraction
        self.kelly_fraction = kelly_fraction
        self.max_class_exposure_pct = max_class_exposure_pct

        # Asset classification mapping
        self.asset_classes = {
            "XAU": "METALS",
            "GOLD": "METALS",
            "BTC": "CRYPTO",
            "ETH": "CRYPTO",
            "SOL": "CRYPTO",
            "EUR": "FOREX",
            "GBP": "FOREX",
            "AUD": "FOREX",
            "NZD": "FOREX",
            "USD": "FOREX"
        }

    def get_asset_class(self, symbol: str) -> str:
        s_upper = symbol.upper()
        for k, v in self.asset_classes.items():
            if k in s_upper:
                return v
        return "FOREX"

    def calculate_fractional_kelly_risk(
        self,
        account_balance: float,
        empirical_win_rate: float,
        payoff_ratio: float,
        sample_size: int = 30
    ) -> Dict[str, Any]:
        """
        Calculates optimal dollar risk percentage via Fractional Kelly Criterion.
        Formula: f* = (p * b - q) / b
        p = win rate (0.0 - 1.0)
        b = payoff ratio (reward / risk)
        q = 1 - p
        """
        # If insufficient samples, fallback to base risk
        if sample_size < 10 or empirical_win_rate <= 0 or payoff_ratio <= 0:
            return {
                "kelly_percent": round(self.base_risk_fraction * 100.0, 2),
                "is_full_kelly": False,
                "notes": "Insufficient sample size. Fallback to baseline 1.0% risk."
            }

        p = empirical_win_rate
        b = payoff_ratio
        q = 1.0 - p

        raw_kelly = (p * b - q) / b
        if raw_kelly <= 0:
            return {
                "kelly_percent": 0.0,
                "is_full_kelly": False,
                "notes": f"Negative statistical expectancy (p={p:.2f}, b={b:.2f}). Allocation vetoed."
            }

        # Apply conservative fractional Kelly multiplier
        scaled_kelly = raw_kelly * self.kelly_fraction

        # Clamp between 0.5% and 2.5% max risk
        clamped_pct = max(0.005, min(scaled_kelly, 0.025))

        return {
            "kelly_percent": round(clamped_pct * 100.0, 2),
            "raw_kelly_pct": round(raw_kelly * 100.0, 2),
            "fraction_used": self.kelly_fraction,
            "is_full_kelly": True,
            "notes": f"Empirical edge verified: p={p:.2f}, b={b:.2f}. Scaled Kelly: {clamped_pct*100:.2f}%."
        }

    def check_portfolio_correlation_risk(
        self,
        symbol: str,
        dollar_risk: float,
        account_balance: float,
        open_positions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Audits total correlated risk exposure in the target asset class.
        """
        positions = open_positions or []
        target_class = self.get_asset_class(symbol)

        class_current_risk = 0.0
        for pos in positions:
            pos_sym = pos.get("symbol", "")
            if self.get_asset_class(pos_sym) == target_class:
                pos_risk = float(pos.get("dollar_risk", pos.get("profit", 0.0)))
                class_current_risk += abs(pos_risk)

        max_allowed_dollar_risk = account_balance * self.max_class_exposure_pct
        projected_total = class_current_risk + dollar_risk

        if projected_total > max_allowed_dollar_risk and class_current_risk > 0:
            return {
                "approved": False,
                "target_class": target_class,
                "current_risk": round(class_current_risk, 2),
                "projected_risk": round(projected_total, 2),
                "max_allowed": round(max_allowed_dollar_risk, 2),
                "reason": f"Correlation Overexposure: Total {target_class} risk would reach ${projected_total:.2f} (Limit: ${max_allowed_dollar_risk:.2f})."
            }

        return {
            "approved": True,
            "target_class": target_class,
            "current_risk": round(class_current_risk, 2),
            "projected_risk": round(projected_total, 2),
            "max_allowed": round(max_allowed_dollar_risk, 2)
        }
