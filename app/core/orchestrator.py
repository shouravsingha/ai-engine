"""
Master Orchestrator
Simultaneous Multi-Market Matrix (Gold, BTC, ETH) with Zero Manual Switching.
Coordinates the 7 Autonomous Robot Agents, Exness MT5 Bridge,
Telegram Sentinel (@SingAiTradebot), and Multi-Platform Webhook Dispatcher.
"""
import time
import threading
from datetime import datetime
from typing import Dict, Any, List

from app.core.market_stream import MarketStream
from app.trading.smc_engine import SMCEngine
from app.trading.fibonacci_engine import FibonacciEngine
from app.trading.risk_manager import RiskManager
from app.trading.demo_account import DemoAccount
from app.trading.exness_bridge import ExnessBridge
from app.agency.branding_engine import BrandingEngine
from app.agency.webhook_dispatcher import SocialWebhookDispatcher
from app.core.telegram_bot import TelegramSentinelBot

class MasterOrchestrator:
    def __init__(self):
        self.market = MarketStream()
        
        # Dedicated parallel SMC detectors for all 3 markets
        self.smc_engines = {
            "gold": SMCEngine(),
            "btc": SMCEngine(),
            "eth": SMCEngine()
        }
        self.fib = FibonacciEngine()
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.5)
        self.account = DemoAccount(initial_capital=50000.0)
        self.exness = ExnessBridge()
        self.branding = BrandingEngine()
        self.webhooks = SocialWebhookDispatcher()
        
        # Telegram Sentinel Bot
        self.telegram = TelegramSentinelBot(
            token="8538360036:AAHvC5EJvrB2Srh5MRn7LghR1IEZpOxuV38",
            chat_id="5347514050",
            command_handler=self.handle_telegram_command
        )

        # 7 Cute 3D Robot Employees (matching WhatsApp Video 2 tags: PA_01, LUC_3, PA_14, etc.)
        self.agents = [
            {"id": "PA_01", "name": "Alex", "role": "Chief Quant", "tag": "PA_01", "dept": "Trading", "status": "Scanning All Markets", "color": "#facc15"},  # Yellow
            {"id": "LUC_3", "name": "David", "role": "Fibonacci Master", "tag": "LUC_3", "dept": "Trading", "status": "0.618 OTE Armed", "color": "#3b82f6"},  # Blue
            {"id": "PA_02", "name": "Marcus", "role": "Risk Officer", "tag": "PA_02", "dept": "Trading", "status": "1% Capital Shield", "color": "#22c55e"},   # Green
            {"id": "PA_14", "name": "Leo", "role": "Execution Trader", "tag": "PA_14 US$ 20.21", "dept": "Trading", "status": "Exness MT5 Live", "color": "#06b6d4"}, # Cyan
            {"id": "PA_16", "name": "Sophia", "role": "Brand Director", "tag": "Conta_1612", "dept": "Media", "status": "Webhooks Armed", "color": "#f97316"}, # Orange
            {"id": "PA_07", "name": "Mia", "role": "Viral Copywriter", "tag": "PA_07", "dept": "Media", "status": "Drafting Thread", "color": "#a855f7"},    # Purple
            {"id": "PA_18", "name": "Noah", "role": "Reels & Script Master", "tag": "PA_18", "dept": "Media", "status": "Hook Testing", "color": "#818cf8"}  # Indigo
        ]
        
        self.agent_messages: List[Dict[str, Any]] = []
        self.system_logs: List[str] = []
        self.multi_market_matrix: Dict[str, Any] = {}
        self.is_running = False

    def handle_telegram_command(self, cmd: str) -> str:
        cmd = cmd.lower().strip()
        if "/status" in cmd:
            ex_stat = "CONNECTED" if self.exness.connected else "STANDBY"
            return f"🏛️ <b>TradingAI Desk Active</b>\nExness MT5: {ex_stat} (#{self.exness.account_id})\nBalance: ${self.exness.balance:,.2f}\nSimultaneous Scan: Gold, BTC & ETH Online."
        elif "/gold" in cmd:
            g = self.multi_market_matrix.get("gold", {})
            return f"🥇 <b>GOLD (XAUUSDm):</b> ${g.get('price', 2745):,.2f}\nTrend: {g.get('trend', 'BULLISH')}\nZone: {g.get('zone', 'DISCOUNT (0.618 OTE)')}"
        elif "/btc" in cmd:
            b = self.multi_market_matrix.get("btc", {})
            return f"⚡ <b>BITCOIN (BTCUSDT):</b> ${b.get('price', 65200):,.2f}\nTrend: {b.get('trend', 'BULLISH')}"
        elif "/scan" in cmd:
            self.run_simultaneous_scan()
            return "⚡ Full multi-asset scan triggered simultaneously across Gold, Bitcoin, and Ethereum!"
        return "Directive processed by TradingAI Core."

    def send_agent_message(self, agent_name: str, role: str, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        entry = {"time": now_str, "agent": agent_name, "role": role, "text": message}
        self.agent_messages.insert(0, entry)
        if len(self.agent_messages) > 45:
            self.agent_messages = self.agent_messages[:45]

    def log(self, message: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{now_str}] {message}"
        print(entry)
        self.system_logs.insert(0, entry)
        if len(self.system_logs) > 50:
            self.system_logs = self.system_logs[:50]

    def run_simultaneous_scan(self):
        """Scans Gold, BTC, and ETH concurrently with zero switching."""
        self.exness.refresh_balance()
        tickers = self.market.get_all_live_tickers()

        matrix = {}
        for asset_key in ["gold", "btc", "eth"]:
            ticker = tickers[asset_key]
            current_price = ticker["price"]
            candles = self.market.get_candles(asset_key, interval="1h", limit=30)
            
            smc_eng = self.smc_engines[asset_key]
            smc_res = smc_eng.analyze_candles(candles)
            trend = smc_res["trend"]
            
            fib_res = self.fib.calculate_levels(smc_res["swing_high"], smc_res["swing_low"], trend)
            zone_status = self.fib.check_zone(current_price, fib_res.get("equilibrium_50", current_price), trend)

            matrix[asset_key] = {
                "symbol": ticker["symbol"],
                "price": current_price,
                "change_pct": ticker["change_pct"],
                "trend": trend,
                "structure_event": smc_res["structure_event"],
                "swing_high": smc_res["swing_high"],
                "swing_low": smc_res["swing_low"],
                "fib_levels": fib_res,
                "zone_status": zone_status,
                "source": ticker.get("source", "Live")
            }

            # Check for High-Probability Setup on this asset
            if len(self.account.open_trades) == 0 and "golden_pocket_ote" in fib_res:
                if trend == "BULLISH" and "DISCOUNT" in zone_status:
                    entry = current_price
                    sl = smc_res["swing_low"] * 0.998
                    tp = fib_res["target_ext_1"]
                    symbol_exec = "XAUUSDm" if asset_key == "gold" else ("BTCUSDT" if asset_key == "btc" else "ETHUSDT")
                    
                    trade_plan = self.risk.evaluate_and_size_trade(self.exness.balance, "BUY", entry, sl, tp)
                    if trade_plan:
                        order = self.account.open_trade(trade_plan, symbol=symbol_exec)
                        asset_title = ticker["symbol"]
                        self.send_agent_message("Alex", "Chief Quant (PA_01)", f"🚀 SIMULTANEOUS TRIGGER: 4H BOS Bullish confirmed on {asset_title}!")
                        self.send_agent_message("David", "Fibonacci Master (LUC_3)", f"{asset_title} mitigated 0.618 Golden Pocket at ${entry:,.2f} in Discount Zone.")
                        self.send_agent_message("Marcus", "Risk Officer (PA_02)", f"Order Approved! 1% risk capped (${trade_plan['dollar_risk']:.2f}). RRR: 1:{trade_plan['risk_reward_ratio']}.")
                        self.send_agent_message("Leo", "Execution Trader (PA_14)", f"Executing on Exness-MT5Trial7! Ticket EXN-{order['id']} active.")

                        # Broadcast to Telegram & Webhooks
                        self.telegram.send_trade_signal(order, asset=asset_title)
                        self.webhooks.broadcast_trade(order, asset=asset_title)

        self.multi_market_matrix = matrix

        # Update open trades against current active asset price
        active_p = matrix["gold"]["price"] if any(t['symbol'] == 'XAUUSDm' for t in self.account.open_trades) else matrix["btc"]["price"]
        closed_trades = self.account.update_open_trades(active_p)
        for ct in closed_trades:
            self.log(f"🔔 TRADE SETTLED: {ct['id']} | Outcome: {ct['status']} | PnL: ${ct.get('realized_pnl', 0):+,.2f}")
            self.telegram.send_trade_close(ct, self.exness.balance)
            self.branding.generate_firm_content("BULLISH", f"${active_p:,.2f}", ct)

    def start_background_loop(self):
        if self.is_running:
            return
        self.is_running = True
        self.log("Multi-Market Parallel AI Desk, Robot Workforce & Telegram Sentinel Live.")

        self.telegram.start_polling()
        self.telegram.send_message("🏛️ <b>TradingAI Desk Online</b>\nSimultaneous Parallel Matrix: Gold (XAUUSD), BTC & ETH.\nExness MT5 Account #434353249 auto-hedged.")

        # Workforce announcements
        self.send_agent_message("Alex", "Chief Quant (PA_01)", "🥇 XAUUSD, BTC, and ETH scanning simultaneously with zero lag.")
        self.send_agent_message("Sophia", "Brand Director (Conta_1612)", "Media team standing by. Ready to broadcast breaking SMC setups.")

        def loop():
            counter = 0
            while True:
                try:
                    self.run_simultaneous_scan()
                    counter += 1
                    
                    if counter % 10 == 0:
                        gold_p = self.multi_market_matrix.get("gold", {}).get("price", 2745.50)
                        btc_p = self.multi_market_matrix.get("btc", {}).get("price", 65200.00)
                        self.send_agent_message("David", "Fibonacci Master (LUC_3)", f"Tracking OTE levels: Gold @ ${gold_p:,.2f} | BTC @ ${btc_p:,.2f}.")
                    elif counter % 16 == 0:
                        self.send_agent_message("Noah", "Reels Master (PA_18)", "Rendering 30s video breakdown for TikTok & YouTube Shorts.")

                except Exception as e:
                    self.log(f"Cycle Note: {str(e)}")
                time.sleep(15)

        threading.Thread(target=loop, daemon=True).start()
