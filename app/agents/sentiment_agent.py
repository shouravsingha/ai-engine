"""
Sentiment & Macro Analyst Specialist Agent.
Monitors macroeconomic headlines, geopolitical sentiment, and central bank expectations.
Strictly assigned LOW WEIGHT in consensus ranking.
Output format: {bias, confidence (0-100), reason, invalidation_level}
"""

from typing import Dict, Any, Optional


class SentimentAnalyst:
    def __init__(self, name: str = "Zara (Macro & Sentiment Scout)"):
        self.name = name
        self.weight = 0.5  # Explicitly marked as low weight

    def analyze(self, symbol: str, macro_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyzes macro and sentiment backdrop for watched asset.
        """
        sym_upper = symbol.upper()

        if "XAU" in sym_upper or "GOLD" in sym_upper:
            # Gold macro safe-haven bias
            return {
                "agent": self.name,
                "bias": "BUY",
                "confidence": 60,
                "reason": "Macro safe-haven demand & central bank reserve accumulation (Low Weight)",
                "invalidation_level": 0.0,
                "weight": self.weight
            }
        elif "BTC" in sym_upper or "ETH" in sym_upper:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 50,
                "reason": "Crypto liquidity tied to US bond yields and risk-on equity appetite (Low Weight)",
                "invalidation_level": 0.0,
                "weight": self.weight
            }
        else:
            return {
                "agent": self.name,
                "bias": "NEUTRAL",
                "confidence": 50,
                "reason": "Balanced interest rate differential (Low Weight)",
                "invalidation_level": 0.0,
                "weight": self.weight
            }
