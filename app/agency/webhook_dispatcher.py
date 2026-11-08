"""
Multi-Platform Automated Social Webhook Dispatcher
Broadcasts high-conviction Gold & Crypto setups and breaking firm news
across Discord, Slack, Make/Zapier, and Social Media endpoints.
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any, List

class SocialWebhookDispatcher:
    def __init__(self):
        self.webhooks = {
            "discord": "",
            "slack": "",
            "generic_social": ""
        }
        self.dispatch_history: List[Dict[str, Any]] = []

    def set_webhook_url(self, platform: str, url: str):
        if platform in self.webhooks:
            self.webhooks[platform] = url.strip()

    def broadcast_trade(self, trade: Dict[str, Any], asset: str = "GOLD (XAUUSD)") -> Dict[str, Any]:
        """Broadcasts trade execution to all configured social webhooks."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        payload = {
            "event": "QUANT_SIGNAL",
            "asset": asset,
            "symbol": trade.get("symbol", "XAUUSDm"),
            "side": trade.get("side", "BUY"),
            "entry": trade.get("entry_price", 0.0),
            "stop_loss": trade.get("stop_loss", 0.0),
            "take_profit": trade.get("take_profit", 0.0),
            "rrr": f"1:{trade.get('rrr', 2.8)}",
            "risk": f"${trade.get('risk_dollar', 500)}",
            "timestamp": now_str
        }

        results = {}
        for platform, url in self.webhooks.items():
            if url:
                try:
                    if platform == "discord":
                        discord_payload = {
                            "embeds": [{
                                "title": f"🏛️ Institutional Signal: {trade.get('side')} {asset}",
                                "color": 0x10b981 if trade.get("side") == "BUY" else 0xf43f5e,
                                "fields": [
                                    {"name": "Entry", "value": f"${trade.get('entry_price'):,.2f}", "inline": True},
                                    {"name": "Stop Loss", "value": f"${trade.get('stop_loss'):,.2f}", "inline": True},
                                    {"name": "Take Profit", "value": f"${trade.get('take_profit'):,.2f}", "inline": True},
                                    {"name": "Strategy", "value": "SMC Golden Pocket (0.618 - 0.786)", "inline": False}
                                ],
                                "footer": {"text": "TradingAI Autonomous Desk"}
                            }]
                        }
                        res = requests.post(url, json=discord_payload, timeout=5)
                        results[platform] = res.status_code == 204 or res.status_code == 200
                    else:
                        res = requests.post(url, json=payload, timeout=5)
                        results[platform] = res.status_code in [200, 201, 202, 204]
                except Exception:
                    results[platform] = False

        record = {
            "type": "TRADE_SIGNAL",
            "asset": asset,
            "dispatched_at": now_str,
            "status": "DISPATCHED",
            "results": results
        }
        self.dispatch_history.insert(0, record)
        if len(self.dispatch_history) > 30:
            self.dispatch_history = self.dispatch_history[:30]

        return record

    def broadcast_branding(self, title: str, text: str) -> Dict[str, Any]:
        """Broadcasts a viral thought-leadership post across social channels."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        payload = {"title": title, "content": text, "timestamp": now_str}
        
        results = {}
        for platform, url in self.webhooks.items():
            if url:
                try:
                    res = requests.post(url, json=payload, timeout=5)
                    results[platform] = res.status_code in [200, 201, 204]
                except Exception:
                    results[platform] = False

        record = {
            "type": "BRANDING_POST",
            "title": title,
            "dispatched_at": now_str,
            "results": results
        }
        self.dispatch_history.insert(0, record)
        return record
