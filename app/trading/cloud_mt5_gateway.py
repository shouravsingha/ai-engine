"""
MetaAPI / Cloud MT5 REST Gateway
Enables 24/7 Cloud Autonomous Trading on Exness without requiring a local laptop to stay turned on.
"""
import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime

class CloudMT5Gateway:
    def __init__(self):
        self.token = os.environ.get("METAAPI_TOKEN", "")
        self.account_id = os.environ.get("EXNESS_ACCOUNT_ID", "434353249")
        self.server = os.environ.get("EXNESS_SERVER", "Exness-MT5Trial7")
        self.password = os.environ.get("EXNESS_PASSWORD", "")
        self.meta_account_id = os.environ.get("METAAPI_ACCOUNT_ID", "")
        self.base_url = "https://mt-client-api-v1.agiliumtrade.agiliumtrade.ai"
        self.provisioning_url = "https://mt-provisioning-api-v1.agiliumtrade.agiliumtrade.ai"
        
        self.connected = False
        self.balance = 20.21
        self.equity = 20.59
        self.floating_pnl = 0.38
        self.currency = "USD"
        self.leverage = "1:2000"
        self.open_positions: List[Dict[str, Any]] = []
        self.last_sync = "Initializing..."

    def is_configured(self) -> bool:
        return bool(self.token and (self.meta_account_id or (self.account_id and self.password)))

    def get_headers(self) -> Dict[str, str]:
        return {
            "auth-token": self.token,
            "Content-Type": "application/json"
        }

    def ensure_cloud_account(self) -> bool:
        """Finds or registers the Exness MT5 account on MetaAPI cloud provisioning."""
        if not self.token:
            return False
        if self.meta_account_id:
            return True

        try:
            # 1. Check existing accounts on MetaAPI
            res = requests.get(f"{self.provisioning_url}/users/current/accounts", headers=self.get_headers(), timeout=8)
            if res.status_code == 200:
                accounts = res.json()
                for acc in accounts:
                    if str(acc.get("login")) == str(self.account_id):
                        self.meta_account_id = acc.get("id")
                        print(f"[CLOUD MT5] Found existing cloud account ID: {self.meta_account_id}")
                        return True

            # 2. Provision new cloud account if not yet registered
            if self.password and self.account_id:
                payload = {
                    "name": f"TradingAI Exness {self.account_id}",
                    "type": "cloud",
                    "login": str(self.account_id),
                    "password": str(self.password),
                    "server": str(self.server),
                    "platform": "mt5",
                    "magic": 202611
                }
                res = requests.post(f"{self.provisioning_url}/users/current/accounts", json=payload, headers=self.get_headers(), timeout=12)
                if res.status_code in (200, 201):
                    data = res.json()
                    self.meta_account_id = data.get("id")
                    print(f"[CLOUD MT5] Provisioned new cloud account ID: {self.meta_account_id}")
                    # Deploy to cloud server
                    requests.post(f"{self.provisioning_url}/users/current/accounts/{self.meta_account_id}/deploy", headers=self.get_headers(), timeout=8)
                    return True
        except Exception as e:
            print(f"[CLOUD MT5 Init Error] {e}")

        return False

    def sync_telemetry(self) -> Dict[str, Any]:
        """Pulls real-time 24/7 balance, equity, and live positions directly from broker servers."""
        if not self.is_configured():
            return {"status": "unconfigured"}

        if not self.meta_account_id:
            if not self.ensure_cloud_account():
                return {"status": "provisioning_required"}

        try:
            # Pull Account Info
            acc_url = f"{self.base_url}/users/current/accounts/{self.meta_account_id}/account-information"
            res = requests.get(acc_url, headers=self.get_headers(), timeout=6)
            if res.status_code == 200:
                acc_data = res.json()
                self.balance = round(float(acc_data.get("balance", self.balance)), 2)
                self.equity = round(float(acc_data.get("equity", self.equity)), 2)
                self.currency = acc_data.get("currency", "USD")
                self.leverage = f"1:{acc_data.get('leverage', 2000)}"
                self.connected = True

            # Pull Open Positions
            pos_url = f"{self.base_url}/users/current/accounts/{self.meta_account_id}/positions"
            p_res = requests.get(pos_url, headers=self.get_headers(), timeout=6)
            if p_res.status_code == 200:
                pos_list = p_res.json()
                self.open_positions = []
                total_pnl = 0.0
                for p in pos_list:
                    side = "BUY" if "BUY" in p.get("type", "") else "SELL"
                    prof = round(float(p.get("profit", 0.0)), 2)
                    total_pnl += prof
                    self.open_positions.append({
                        "ticket": p.get("id"),
                        "symbol": p.get("symbol"),
                        "side": side,
                        "volume": float(p.get("volume", 0.01)),
                        "open_price": float(p.get("openPrice", 0.0)),
                        "current_price": float(p.get("currentPrice", 0.0)),
                        "sl": float(p.get("stopLoss", 0.0)),
                        "tp": float(p.get("takeProfit", 0.0)),
                        "profit": prof
                    })
                self.floating_pnl = round(total_pnl, 2)
                self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                return {"status": "success", "balance": self.balance, "equity": self.equity, "open_positions": self.open_positions}
        except Exception as e:
            print(f"[CLOUD MT5 Sync Error] {e}")

        return {"status": "error"}

    def execute_live_order(self, symbol: str, side: str, volume: float = 0.01, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Executes real trade directly in cloud via Exness broker gateway."""
        if not self.is_configured() or not self.meta_account_id:
            return {"status": "error", "message": "Cloud gateway not provisioned"}

        try:
            trade_url = f"{self.base_url}/users/current/accounts/{self.meta_account_id}/trade"
            action_type = "ORDER_TYPE_BUY" if side.upper() == "BUY" else "ORDER_TYPE_SELL"
            payload = {
                "actionType": action_type,
                "symbol": symbol,
                "volume": float(volume),
                "stopLoss": float(sl) if sl > 0 else None,
                "takeProfit": float(tp) if tp > 0 else None,
                "comment": "TradingAI 24/7 Cloud Execution"
            }
            res = requests.post(trade_url, json=payload, headers=self.get_headers(), timeout=10)
            if res.status_code in (200, 201):
                data = res.json()
                self.sync_telemetry()
                return {
                    "status": "success",
                    "orderId": data.get("orderId"),
                    "numericCode": data.get("numericCode"),
                    "message": f"Successfully executed {side} {volume} {symbol} 24/7 on Exness MT5"
                }
            else:
                return {"status": "failed", "detail": res.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close_position(self, position_id: Any) -> Dict[str, Any]:
        """Closes a position in the cloud."""
        if not self.is_configured() or not self.meta_account_id:
            return {"status": "error", "message": "Cloud gateway not provisioned"}

        try:
            trade_url = f"{self.base_url}/users/current/accounts/{self.meta_account_id}/trade"
            payload = {
                "actionType": "POSITION_CLOSE_ID",
                "positionId": str(position_id)
            }
            res = requests.post(trade_url, json=payload, headers=self.get_headers(), timeout=10)
            if res.status_code in (200, 201):
                self.sync_telemetry()
                return {"status": "success", "ticket": position_id}
            else:
                return {"status": "failed", "detail": res.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close_all_positions(self) -> Dict[str, Any]:
        """Emergency flatten all positions in cloud."""
        closed = []
        for p in list(self.open_positions):
            c_res = self.close_position(p.get("ticket"))
            closed.append(c_res)
        return {"status": "success", "closed": closed}
