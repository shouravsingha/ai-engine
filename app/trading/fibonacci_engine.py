"""
Fibonacci Retracement & Optimal Trade Entry (OTE) Engine
Calculates Equilibrium (50%), Discount vs Premium, and Golden Pocket (0.618 - 0.786).
"""
from typing import Dict, Any

class FibonacciEngine:
    def calculate_levels(self, swing_high: float, swing_low: float, trend: str) -> Dict[str, Any]:
        """
        Maps institutional Fibonacci retracement and extensions.
        """
        diff = swing_high - swing_low
        if diff <= 0:
            return {}

        equilibrium = swing_low + (diff * 0.50)

        if trend == "BULLISH":
            # Retracement from high down to discount
            fib_382 = swing_high - (diff * 0.382)
            fib_500 = equilibrium
            fib_618 = swing_high - (diff * 0.618)
            fib_786 = swing_high - (diff * 0.786)
            tp_ext1 = swing_high + (diff * 0.27)
            tp_ext2 = swing_high + (diff * 0.618)
            
            ote_zone = {"low": round(fib_786, 2), "high": round(fib_618, 2)}
        else:
            # Retracement from low up to premium
            fib_382 = swing_low + (diff * 0.382)
            fib_500 = equilibrium
            fib_618 = swing_low + (diff * 0.618)
            fib_786 = swing_low + (diff * 0.786)
            tp_ext1 = swing_low - (diff * 0.27)
            tp_ext2 = swing_low - (diff * 0.618)
            
            ote_zone = {"low": round(fib_618, 2), "high": round(fib_786, 2)}

        return {
            "equilibrium_50": round(equilibrium, 2),
            "golden_pocket_ote": ote_zone,
            "fib_618": round(fib_618, 2),
            "fib_786": round(fib_786, 2),
            "target_ext_1": round(tp_ext1, 2),
            "target_ext_2": round(tp_ext2, 2)
        }

    def check_zone(self, price: float, equilibrium: float, trend: str) -> str:
        """Determines if current price is in Discount or Premium."""
        if price < equilibrium:
            return "DISCOUNT (PRIME BUY ZONE)" if trend == "BULLISH" else "DISCOUNT"
        else:
            return "PREMIUM (PRIME SELL ZONE)" if trend == "BEARISH" else "PREMIUM"
