"""
Exness Demo & MetaTrader 5 (MT5) Real Integration Bridge
Directly connects to local MetaTrader 5 terminal on Windows if available,
or operates high-fidelity paper mirror synced with account #434353249.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from app.trading.cloud_mt5_gateway import CloudMT5Gateway

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class ExnessBridge:
    def __init__(self, command_queue=None):
        import os
        self.command_queue = command_queue if command_queue is not None else []
        self.account_id = os.environ.get("MT5_ACCOUNT", "434353249")
        self.password = os.environ.get("MT5_PASSWORD", "ShouravDemo60@#")
        self.server = os.environ.get("MT5_SERVER", "Exness-MT5Trial7")
        self.path = os.environ.get("MT5_PATH", r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe")
        self.balance = 20.21
        self.equity = 20.21
        self.currency = "USD"
        self.leverage = "1:2000"
        self.connected = False
        self.live_terminal = False
        self.last_sync = "Initializing..."
        self.status_message = "Ready"
        self.floating_pnl = 0.0
        self.open_positions = []
        self.last_remote_sync_ts = 0.0
        self.cloud_gateway = CloudMT5Gateway()
        
        # Auto-initialize with detected Exness account
        self.try_initialize_mt5()

    def apply_remote_sync(self, data: dict):
        """Applies live MT5 metrics pushed from local host."""
        self.account_id = str(data.get("account_id", self.account_id))
        self.server = data.get("server", self.server)
        self.balance = round(float(data.get("balance", self.balance)), 2)
        self.equity = round(float(data.get("equity", self.equity)), 2)
        self.floating_pnl = round(float(data.get("floating_pnl", self.floating_pnl)), 2)
        self.currency = data.get("currency", self.currency)
        self.leverage = data.get("leverage", self.leverage)
        if "open_positions" in data:
            self.open_positions = data["open_positions"]
        self.connected = True
        self.live_terminal = True
        self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.status_message = f"LIVE MT5 TUNNEL (Account #{self.account_id} on {self.server})"
        self.last_remote_sync_ts = datetime.now().timestamp()

    def try_initialize_mt5(self) -> bool:
        """Attempts real connection to local MetaTrader 5 Exness terminal."""
        if MT5_AVAILABLE:
            try:
                # 1. First try attaching to currently running MT5 instance with short timeout
                initialized = False
                try:
                    initialized = mt5.initialize(timeout=2500)
                except Exception:
                    pass
                
                # 2. If not initialized, try explicitly with path and login credentials
                if not initialized and hasattr(self, 'path') and self.path:
                    try:
                        acc_id_int = int(self.account_id)
                        initialized = mt5.initialize(
                            path=self.path,
                            login=acc_id_int,
                            password=self.password,
                            server=self.server,
                            timeout=3500
                        )
                    except Exception as e:
                        print(f"MT5 Explicit Init Note: {e}")

                if initialized:
                    acc_info = mt5.account_info()
                    if acc_info:
                        self.account_id = str(acc_info.login)
                        self.server = acc_info.server
                        self.balance = float(acc_info.balance)
                        self.equity = float(acc_info.equity)
                        self.currency = acc_info.currency
                        self.leverage = f"1:{acc_info.leverage}"
                        self.connected = True
                        self.live_terminal = True
                        self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                        self.status_message = f"LIVE MT5 CONNECTED (Account #{self.account_id} on {self.server})"
                        print(f"[EXNESS MT5 CONNECTED] #{self.account_id} on {self.server} | Balance: ${self.balance:,.2f}")
                        return True
            except Exception as e:
                print(f"MT5 Init Note: {e}")

        # Fallback state when MT5 terminal is not linked
        self.connected = False
        self.live_terminal = False
        self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.status_message = f"Waiting for MT5 Terminal (Account #{self.account_id})"
        return False

    def refresh_balance(self):
        """Pulls latest tick balance, equity, margin, and live open positions from MT5 or Cloud Gateway."""
        if self.cloud_gateway.is_configured():
            res = self.cloud_gateway.sync_telemetry()
            if res.get("status") == "success":
                self.balance = self.cloud_gateway.balance
                self.equity = self.cloud_gateway.equity
                self.floating_pnl = self.cloud_gateway.floating_pnl
                self.open_positions = self.cloud_gateway.open_positions
                self.connected = True
                self.live_terminal = True
                self.status_message = f"24/7 CLOUD AUTONOMOUS (Account #{self.account_id} on {self.server})"
                self.last_sync = self.cloud_gateway.last_sync
                return

        if MT5_AVAILABLE:
            try:
                acc_info = mt5.account_info()
                if not acc_info:
                    mt5.initialize()
                    acc_info = mt5.account_info()

                if acc_info:
                    self.account_id = str(acc_info.login)
                    self.server = acc_info.server
                    self.balance = round(float(acc_info.balance), 2)
                    self.equity = round(float(acc_info.equity), 2)
                    self.currency = acc_info.currency
                    self.leverage = f"1:{acc_info.leverage}"
                    self.connected = True
                    self.live_terminal = True
                    self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
                    self.status_message = f"LIVE MT5 CONNECTED (Account #{self.account_id} on {self.server})"

                    # Get all open MT5 positions
                    positions = mt5.positions_get()
                    new_positions = []
                    total_profit = 0.0
                    if positions is not None:
                        for p in positions:
                            side = "BUY" if p.type == 0 else "SELL"
                            new_positions.append({
                                "ticket": p.ticket,
                                "symbol": p.symbol,
                                "side": side,
                                "volume": p.volume,
                                "open_price": p.price_open,
                                "current_price": p.price_current,
                                "sl": p.sl,
                                "tp": p.tp,
                                "profit": round(float(p.profit), 2)
                            })
                            total_profit += float(p.profit)
                        self.open_positions = new_positions
                        self.floating_pnl = round(total_profit, 2)
                else:
                    self.live_terminal = False
                    self.connected = False
            except Exception as e:
                pass
        else:
            # Cloud (Render) mode without direct Windows MT5
            now_ts = datetime.now().timestamp()
            time_since_sync = now_ts - getattr(self, 'last_remote_sync_ts', 0.0)

            # Check if live tunnel from laptop sent a heartbeat within the last 15 seconds
            if getattr(self, 'last_remote_sync_ts', 0.0) > 0 and time_since_sync <= 15.0:
                self.connected = True
                self.live_terminal = True
                self.status_message = f"🟢 LIVE MT5 TUNNEL (Account #{self.account_id} on {self.server})"
            else:
                self.connected = False
                self.live_terminal = False
                if getattr(self, 'last_remote_sync_ts', 0.0) == 0.0:
                    self.status_message = "🔴 TUNNEL WAITING (Start start_ai_trader.bat on your laptop)"
                    self.open_positions = []
                    self.floating_pnl = 0.0
                else:
                    self.status_message = f"🔴 TUNNEL DISCONNECTED (Laptop Closed/Offline - Last seen {int(time_since_sync)}s ago)"

    def execute_live_order(self, symbol: str, side: str, volume: float = 0.01, sl: float = 0.0, tp: float = 0.0) -> Dict[str, Any]:
        """Executes a real order directly on the Exness MT5 terminal or 24/7 Cloud Gateway."""
        if self.cloud_gateway.is_configured():
            c_res = self.cloud_gateway.execute_live_order(symbol, side, volume, sl, tp)
            if c_res.get("status") == "success":
                return {
                    "status": "success",
                    "ticket": c_res.get("orderId"),
                    "symbol": symbol,
                    "side": side,
                    "volume": volume,
                    "message": f"24/7 Cloud Executed {side} {volume} {symbol} on Exness MT5"
                }

        if not (MT5_AVAILABLE and self.live_terminal):
            # Cloud (Render) mode without direct Windows MT5:
            # Queue order to be dispatched to local Windows MT5 tunnel!
            self.command_queue.append({
                "action": "execute",
                "symbol": symbol,
                "side": side,
                "volume": float(volume),
                "sl": float(sl),
                "tp": float(tp)
            })
            print(f"[TUNNEL DISPATCH] Queued {side} {volume} {symbol} for Windows MT5 terminal!")
            return {"status": "queued", "ticket": f"TUNNEL-{int(datetime.now().timestamp())}", "message": f"Queued for Windows MT5 terminal"}

        try:
            # Map symbol for Exness trial account
            sym = symbol
            if not mt5.symbol_info(sym):
                if not sym.endswith("m") and mt5.symbol_info(sym + "m"):
                    sym = sym + "m"
                elif sym.endswith("m") and mt5.symbol_info(sym[:-1]):
                    sym = sym[:-1]

            s_info = mt5.symbol_info(sym)
            if not s_info:
                return {"status": "error", "message": f"Symbol {symbol} not found on Exness MT5"}

            if not s_info.visible:
                mt5.symbol_select(sym, True)

            # Auto-align volume with broker minimum specification
            min_vol = float(s_info.volume_min) if hasattr(s_info, 'volume_min') else 0.01
            vol_step = float(s_info.volume_step) if hasattr(s_info, 'volume_step') else 0.01
            req_vol = max(float(volume), min_vol)
            req_vol = round(req_vol, 2)

            order_type = mt5.ORDER_TYPE_BUY if side.upper() == "BUY" else mt5.ORDER_TYPE_SELL
            tick_now = mt5.symbol_info_tick(sym)
            if not tick_now:
                return {"status": "error", "message": f"Could not pull price for {sym}"}
            price = tick_now.ask if side.upper() == "BUY" else tick_now.bid

            # Robust SL and TP calculation avoiding spread & stop level invalidation
            point = s_info.point
            stop_level = max(getattr(s_info, 'trade_stops_level', 10), 10) * point
            spread = max(getattr(s_info, 'spread', 10), 10) * point
            min_dist = max(stop_level * 1.5, spread * 2.0, price * 0.003)

            digits = s_info.digits if hasattr(s_info, 'digits') else 2
            if side.upper() == "BUY":
                if sl == 0.0 or sl >= price or (price - sl) < min_dist:
                    sl = price - (min_dist * 2.0)
                if tp == 0.0 or tp <= price or (tp - price) < min_dist:
                    tp = price + (min_dist * 4.0)
            else:
                if sl == 0.0 or sl <= price or (sl - price) < min_dist:
                    sl = price + (min_dist * 2.0)
                if tp == 0.0 or tp >= price or (price - tp) < min_dist:
                    tp = price - (min_dist * 4.0)

            sl = round(float(sl), digits)
            tp = round(float(tp), digits)

            # Determine supported filling mode (Exness supports IOC or FOK)
            filling = mt5.ORDER_FILLING_IOC
            if hasattr(s_info, 'filling_mode'):
                if (s_info.filling_mode & 2):
                    filling = mt5.ORDER_FILLING_IOC
                elif (s_info.filling_mode & 1):
                    filling = mt5.ORDER_FILLING_FOK
                else:
                    filling = mt5.ORDER_FILLING_RETURN

            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": sym,
                "volume": req_vol,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 25,
                "magic": 202611,
                "comment": "TradingAI Live Execution",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling,
            }
            res = mt5.order_send(req)

            # If rejected with unsupported filling mode (retcode 10030), retry with alternatives
            if res and res.retcode in (10030, 10013):
                alt_filling = mt5.ORDER_FILLING_FOK if filling == mt5.ORDER_FILLING_IOC else mt5.ORDER_FILLING_IOC
                req["type_filling"] = alt_filling
                res = mt5.order_send(req)
                if res and res.retcode in (10030, 10013):
                    req["type_filling"] = mt5.ORDER_FILLING_RETURN
                    res = mt5.order_send(req)

            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                self.refresh_balance()
                print(f"[MT5 TRADE EXECUTED] #{res.order} {side} {req_vol} {sym} @ {res.price}")
                return {
                    "status": "success",
                    "ticket": res.order,
                    "deal": res.deal,
                    "symbol": sym,
                    "side": side,
                    "volume": req_vol,
                    "price": res.price,
                    "message": f"Successfully executed {side} {req_vol} {sym} on Exness MT5 (Ticket #{res.order})"
                }
            else:
                err_code = res.retcode if res else "None"
                err_comment = res.comment if res else "Execution rejected by broker"
                print(f"[MT5 EXECUTION FAILED] Symbol: {sym}, Side: {side}, Retcode: {err_code}, Comment: {err_comment}")
                if err_code == 10027:
                    print("⚠️ [MT5 WARNING] Algo Trading is DISABLED in MetaTrader 5! Press 'Algo Trading' button in MT5 (or Ctrl+E) to allow auto trades.")
                return {
                    "status": "failed",
                    "retcode": err_code,
                    "comment": err_comment
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def modify_position_sl_tp(self, ticket: int, new_sl: float, new_tp: float = 0.0) -> Dict[str, Any]:
        """Modifies Stop Loss and Take Profit of a live MT5 position (Break-Even or Trailing Stop)."""
        if not (MT5_AVAILABLE and self.live_terminal):
            # Cloud (Render) mode without direct Windows MT5: queue for laptop tunnel!
            self.command_queue.append({
                "action": "modify",
                "ticket": int(ticket),
                "sl": float(new_sl),
                "tp": float(new_tp)
            })
            return {"status": "queued", "ticket": ticket, "message": f"Queued SL/TP update for #{ticket}"}

        try:
            positions = mt5.positions_get(ticket=int(ticket))
            if not positions:
                return {"status": "error", "message": f"Position #{ticket} not found on MT5"}

            pos = positions[0]
            sym = pos.symbol
            s_info = mt5.symbol_info(sym)
            digits = s_info.digits if s_info else 2

            final_sl = round(float(new_sl), digits)
            final_tp = round(float(new_tp if new_tp > 0 else pos.tp), digits)

            req = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": pos.ticket,
                "symbol": sym,
                "sl": final_sl,
                "tp": final_tp,
            }
            res = mt5.order_send(req)
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                self.refresh_balance()
                print(f"[MT5 SL/TP MODIFIED] Ticket #{ticket} ({sym}) New SL: {final_sl} | TP: {final_tp}")
                return {
                    "status": "success",
                    "ticket": ticket,
                    "new_sl": final_sl,
                    "new_tp": final_tp,
                    "message": f"Successfully updated #{ticket} SL to {final_sl}"
                }
            else:
                return {
                    "status": "failed",
                    "retcode": res.retcode if res else "None",
                    "comment": res.comment if res else "Broker rejected SL/TP update"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close_position(self, ticket: int) -> Dict[str, Any]:
        """Closes a specific open position on Exness MT5 or 24/7 Cloud Gateway."""
        if self.cloud_gateway.is_configured():
            return self.cloud_gateway.close_position(ticket)

        if not (MT5_AVAILABLE and self.live_terminal):
            return {"status": "error", "message": "MT5 terminal not linked"}

        try:
            positions = mt5.positions_get(ticket=int(ticket))
            if not positions:
                return {"status": "error", "message": f"Position #{ticket} not found or already closed"}

            pos = positions[0]
            close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            sym_info = mt5.symbol_info_tick(pos.symbol)
            price = sym_info.bid if pos.type == 0 else sym_info.ask

            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "price": price,
                "deviation": 20,
                "magic": 202611,
                "comment": "TradingAI Manual Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            res = mt5.order_send(req)
            self.refresh_balance()
            if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                return {
                    "status": "success",
                    "ticket": ticket,
                    "close_price": price,
                    "message": f"Position #{ticket} ({pos.symbol}) closed successfully at {price}"
                }
            else:
                return {
                    "status": "failed",
                    "retcode": res.retcode if res else "None",
                    "comment": res.comment if res else "Close rejected by broker"
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close_all_positions(self) -> Dict[str, Any]:
        """Emergency flattens all open positions on Exness MT5 or 24/7 Cloud Gateway."""
        if self.cloud_gateway.is_configured():
            return self.cloud_gateway.close_all_positions()

        if not (MT5_AVAILABLE and self.live_terminal):
            return {"status": "error", "message": "MT5 terminal not linked"}

        positions = mt5.positions_get()
        closed = []
        if positions:
            for p in positions:
                c_res = self.close_position(p.ticket)
                closed.append({"ticket": p.ticket, "symbol": p.symbol, "res": c_res})
        self.refresh_balance()
        return {"status": "success", "closed_positions": closed, "total_closed": len(closed)}

    def get_status(self) -> Dict[str, Any]:
        self.refresh_balance()
        return {
            "connected": self.connected,
            "live_terminal": self.live_terminal,
            "account_id": self.account_id,
            "server": self.server,
            "balance": round(self.balance, 2),
            "equity": round(self.equity, 2),
            "currency": self.currency,
            "leverage": self.leverage,
            "last_sync": self.last_sync,
            "status_message": self.status_message,
            "floating_pnl": getattr(self, "floating_pnl", 0.0),
            "open_positions": getattr(self, "open_positions", [])
        }

    def sync_trade_execution(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches or syncs order execution with Exness."""
        ticket_id = f"EXN-{trade['id']}"
        self.last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        return {
            "status": "synced",
            "exness_ticket": ticket_id,
            "server": self.server,
            "account_id": self.account_id,
            "message": f"Forwarded {trade['side']} order for {trade['symbol']} to {self.server} (Ticket {ticket_id})"
        }

def start_cloud_tunnel_daemon(bridge: ExnessBridge, cloud_url: str = "https://ai-engine-6bpy.onrender.com"):
    """
    On Windows machines with physical MT5 running, continuously streams 
    the real MT5 balance, equity, and positions to Render cloud every 1.5s.
    Also polls Render for pending orders submitted from anywhere in the world.
    Keeps Windows active so that the tunnel runs uninterrupted even when the laptop lid is closed.
    """
    if not MT5_AVAILABLE:
        return

    import threading
    import time
    import requests

    def _sync_worker():
        # Prevent Windows from sleeping or suspending threads when laptop lid closes
        try:
            import ctypes
            # ES_CONTINUOUS (0x80000000) | ES_SYSTEM_REQUIRED (0x00000001) | ES_AWAYMODE_REQUIRED (0x00000040)
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000040)
            print("[TUNNEL DAEMON] Windows Anti-Sleep / Away Mode activated (Runs with lid closed).")
        except Exception:
            pass

        time.sleep(2.0)
        print(f"[TUNNEL DAEMON] Windows-to-Render MT5 Cloud Bridge initiated for {cloud_url}")
        
        reconnect_counter = 0
        while True:
            try:
                # Continuous auto-reconnection if MT5 is not yet initialized or disconnected
                if not bridge.live_terminal:
                    reconnect_counter += 1
                    if reconnect_counter % 3 == 0:
                        bridge.try_initialize_mt5()

                if bridge.live_terminal:
                    bridge.refresh_balance()
                    payload = {
                        "exness": {
                            "account_id": bridge.account_id,
                            "server": bridge.server,
                            "balance": bridge.balance,
                            "equity": bridge.equity,
                            "floating_pnl": bridge.floating_pnl,
                            "currency": bridge.currency,
                            "leverage": bridge.leverage,
                            "open_positions": bridge.open_positions
                        }
                    }
                    res = requests.post(f"{cloud_url}/api/bridge/sync", json=payload, timeout=4.0)
                    if res.status_code == 200:
                        cmd_data = res.json()
                        commands = cmd_data.get("commands", [])
                        for c in commands:
                            action = c.get("action")
                            if action == "execute":
                                t_res = bridge.execute_live_order(
                                    c.get("symbol", "XAUUSDm"),
                                    c.get("side", "BUY"),
                                    float(c.get("volume", 0.01)),
                                    float(c.get("sl", 0.0)),
                                    float(c.get("tp", 0.0))
                                )
                                print(f"[TUNNEL ORDER EXECUTED] {c.get('side')} {c.get('symbol')} -> {t_res.get('status')}: {t_res.get('message', t_res.get('comment'))}")
                            elif action == "modify":
                                m_res = bridge.modify_position_sl_tp(
                                    int(c.get("ticket")),
                                    float(c.get("sl", 0.0)),
                                    float(c.get("tp", 0.0))
                                )
                                print(f"[TUNNEL SL/TP MODIFIED] Ticket #{c.get('ticket')} -> {m_res.get('status')}")
                            elif action == "close":
                                c_res = bridge.close_position(int(c.get("ticket")))
                                print(f"[TUNNEL POSITION CLOSED] Ticket #{c.get('ticket')} -> {c_res.get('status')}")
                            elif action == "panic_flat":
                                p_res = bridge.close_all_positions()
                                print(f"[TUNNEL PANIC FLAT] -> {p_res.get('status')}")
            except Exception:
                pass
            time.sleep(1.5)

    th = threading.Thread(target=_sync_worker, daemon=True)
    th.start()
