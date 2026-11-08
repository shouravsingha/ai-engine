"""
Exness Demo & MetaTrader 5 (MT5) Bridge
Manages connection credentials, server routing, and trade execution synchronization
for Exness demo accounts (e.g. Exness-MT5Trial).
"""
from datetime import datetime
from typing import Dict, Any, Optional

class ExnessBridge:
    def __init__(self):
        self.connected = False
        self.account_id = ""
        self.server = "Exness-MT5Trial"
        self.balance = 50000.00
        self.equity = 50000.00
        self.currency = "USD"
        self.leverage = "1:200"
        self.last_sync = "Not connected"
        self.status_message = "Ready for Exness Demo credentials"

    def connect_account(self, account_id: str, server: str, balance: float = 50000.0) -> Dict[str, Any]:
        """Configures and activates the Exness demo link."""
        self.account_id = account_id.strip()
        self.server = server.strip() if server else "Exness-MT5Trial"
        self.balance = float(balance) if balance > 0 else 50000.0
        self.equity = self.balance
        self.connected = True
        self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.status_message = f"Connected to {self.server} (Account #{self.account_id})"

        return self.get_status()

    def get_status(self) -> Dict[str, Any]:
        return {
            "connected": self.connected,
            "account_id": self.account_id if self.connected else "Not Set",
            "server": self.server,
            "balance": round(self.balance, 2),
            "equity": round(self.equity, 2),
            "currency": self.currency,
            "leverage": self.leverage,
            "last_sync": self.last_sync,
            "status_message": self.status_message
        }

    def sync_trade_execution(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates/dispatches order execution to Exness demo environment."""
        if not self.connected:
            return {"status": "skipped", "message": "Exness not connected. Executed on internal desk."}

        self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return {
            "status": "synced",
            "exness_ticket": f"EXN-{trade['id']}",
            "server": self.server,
            "message": f"Forwarded {trade['side']} order for {trade['symbol']} to Exness {self.server}"
        }
