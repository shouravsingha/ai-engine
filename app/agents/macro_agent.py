"""
Macro Cross-Asset Correlation Agent (PA_05 Zara / Macro Strategist)
Monitors cross-market dynamics: US Dollar Strength (DXY proxy), Gold vs USD correlation,
Crypto beta, and Risk-On / Risk-Off sentiment to ensure trades align with macro capital flows.
"""
from typing import Dict, Any, Optional
import pandas as pd


class MacroCrossAssetAnalyst:
    def __init__(self):
        # Asset class macro sensitivity profiles
        self.asset_profiles = {
            "XAUUSDm": {"class": "METALS", "usd_inverse": True, "safe_haven": True},
            "BTCUSDm": {"class": "CRYPTO", "usd_inverse": True, "risk_asset": True},
            "ETHUSDm": {"class": "CRYPTO", "usd_inverse": True, "risk_asset": True},
            "EURUSDm": {"class": "FOREX", "usd_inverse": True, "risk_asset": False},
            "GBPUSDm": {"class": "FOREX", "usd_inverse": True, "risk_asset": False},
            "USDJPYm": {"class": "FOREX", "usd_inverse": False, "risk_asset": False}
        }

    def analyze_macro_context(
        self,
        symbol: str,
        macro_feed: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes macro context for the given asset symbol.
        macro_feed can include:
        - dxy_bias: 'BULLISH', 'BEARISH', or 'NEUTRAL'
        - risk_sentiment: 'RISK_ON', 'RISK_OFF', or 'NEUTRAL'
        - yields_trend: 'RISING', 'FALLING', or 'STABLE'
        """
        feed = macro_feed or {}
        dxy_bias = feed.get("dxy_bias", "NEUTRAL").upper()
        risk_sentiment = feed.get("risk_sentiment", "NEUTRAL").upper()
        yields_trend = feed.get("yields_trend", "STABLE").upper()

        profile = self.asset_profiles.get(symbol, {"class": "FOREX", "usd_inverse": True, "risk_asset": False})

        macro_bias = "NEUTRAL"
        confidence = 50.0
        reasons = []

        # 1. US Dollar Impact
        if profile["usd_inverse"]:
            if dxy_bias == "BULLISH":
                macro_bias = "SELL"
                confidence += 20.0
                reasons.append("Macro Headwind: Strong DXY pressurizes dollar-denominated assets")
            elif dxy_bias == "BEARISH":
                macro_bias = "BUY"
                confidence += 20.0
                reasons.append("Macro Tailwind: Weak DXY provides institutional liquidity tailwind")
        else:
            if dxy_bias == "BULLISH":
                macro_bias = "BUY"
                confidence += 20.0
                reasons.append("Macro Tailwind: USD base currency strengthens on DXY upside")
            elif dxy_bias == "BEARISH":
                macro_bias = "SELL"
                confidence += 20.0
                reasons.append("Macro Headwind: USD base currency softens on DXY downside")

        # 2. Risk Sentiment Impact (Gold Safe Haven vs Crypto Risk-On)
        if profile.get("safe_haven"):
            if risk_sentiment == "RISK_OFF":
                if macro_bias == "BUY":
                    confidence += 15.0
                else:
                    macro_bias = "BUY"
                    confidence = max(confidence, 65.0)
                reasons.append("Safe-Haven Inflows: Risk-Off regime drives institutional hedging into Gold")
            elif risk_sentiment == "RISK_ON" and yields_trend == "RISING":
                reasons.append("Yield Pressure: Rising opportunity cost and Risk-On sentiment cap Gold upside")

        if profile.get("risk_asset"):
            if risk_sentiment == "RISK_ON":
                if macro_bias == "BUY":
                    confidence += 15.0
                else:
                    macro_bias = "BUY"
                    confidence = max(confidence, 65.0)
                reasons.append("High-Beta Tailwinds: Risk-On appetite stimulates institutional crypto volume")
            elif risk_sentiment == "RISK_OFF":
                macro_bias = "SELL" if macro_bias != "BUY" else "NEUTRAL"
                reasons.append("Deleveraging Pressure: Risk-Off liquidity contraction impacts crypto holdings")

        if not reasons:
            reasons.append("Balanced Macro Flow: DXY and global risk indicators neutral/aligned")

        return {
            "agent": "Macro Cross-Asset Analyst",
            "symbol": symbol,
            "bias": macro_bias,
            "confidence": round(min(confidence, 95.0), 1),
            "weight": 1.25,
            "reasons": reasons,
            "dxy_bias": dxy_bias,
            "risk_sentiment": risk_sentiment
        }
