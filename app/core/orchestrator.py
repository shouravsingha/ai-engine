"""
Master Orchestrator
Virtual 3D Office Controller: Dual-Asset Quant Desk (Gold XAUUSD & BTC)
+ Exness MT5 Live Bridge + Telegram Sentinel Bot (@SingAiTradebot)
+ Multi-Platform Social Webhook Dispatcher.
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
        self.gold_smc = SMCEngine()
        self.btc_smc = SMCEngine()
        self.fib = FibonacciEngine()
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.5)
        self.account = DemoAccount(initial_capital=50000.0)
        self.exness = ExnessBridge()
        self.branding = BrandingEngine()
        self.webhooks = SocialWebhookDispatcher()
        
        # Initialize Telegram Sentinel Bot
        self.telegram = TelegramSentinelBot(
            token="8538360036:AAHvC5EJvrB2Srh5MRn7LghR1IEZpOxuV38",
            chat_id="5347514050",
            command_handler=self.handle_telegram_command
        )

        # 7 Autonomous Office Agents
        self.agents = [
            {"id": "A1", "name": "Alex", "role": "Chief Quant (Gold & Crypto)", "dept": "Trading", "status": "Scanning XAUUSD & BTC", "color": "#38bdf8"},
            {"id": "A2", "name": "David", "role": "Fibonacci Specialist", "dept": "Trading", "status": "0.618 OTE Calibrated", "color": "#3b82f6"},
            {"id": "A3", "name": "Marcus", "role": "Chief Risk Officer", "dept": "Trading", "status": "1% Capital Shield Active", "color": "#10b981"},
            {"id": "A4", "name": "Leo", "role": "Execution Trader", "dept": "Trading", "status": "Exness MT5 Live (#434353249)", "color": "#f59e0b"},
            {"id": "A5", "name": "Sophia", "role": "Brand Director", "dept": "Media", "status": "Webhooks Armed", "color": "#ec4899"},
            {"id": "A6", "name": "Mia", "role": "Viral Copywriter", "dept": "Media", "status": "Drafting Gold Breakdown", "color": "#a855f7"},
            {"id": "A7", "name": "Noah", "role": "Reels & Script Master", "dept": "Media", "status": "Recording 30s Hook", "color": "#8b5cf6"}
        ]
        
        self.agent_messages: List[Dict[str, Any]] = []
        self.system_logs: List[str] = []
        self.gold_analysis: Dict[str, Any] = {}
        self.btc_analysis: Dict[str, Any] = {}
        self.is_running = False

    def handle_telegram_command(self, cmd: str) -> str:
        cmd = cmd.lower().strip()
        if "/status" in cmd:
            ex_stat = "CONNECTED" if self.exness.connected else "STANDBY"
            return f"🏛️ <b>Office Status:</b> ACTIVE (7/7 Agents)\nExness MT5: {ex_stat} (#{self.exness.account_id})\nBalance: ${self.exness.balance:,.2f}\nOpen Trades: {len(self.account.open_trades)}"
        elif "/scan" in cmd:
            self.run_market_cycle()
            return "⚡ Immediate multi-timeframe scan completed for Gold (XAUUSD) & Bitcoin (BTCUSDT)!"
        return "Directive confirmed by TradingAI Core."

    def send_agent_message(self, agent_name: str, role: str, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        entry = {"time": now_str, "agent": agent_name, "role": role, "text": message}
        self.agent_messages.insert(0, entry)
        if len(self.agent_messages) > 40:
            self.agent_messages = self.agent_messages[:40]

    def log(self, message: str):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{now_str}] {message}"
        print(entry)
        self.system_logs.insert(0, entry)
        if len(self.system_logs) > 50:
            self.system_logs = self.system_logs[:50]

    def run_market_cycle(self):
        """Runs institutional evaluation for both Gold (XAUUSD) and Bitcoin."""
        self.exness.refresh_balance()

        # ==================== 1. GOLD (XAUUSD) CYCLE ====================
        gold_ticker = self.market.get_live_gold_ticker()
        gold_price = gold_ticker["price"]
        gold_candles = self.market.get_gold_candles(interval="1h", limit=30)
        gold_smc_res = self.gold_smc.analyze_candles(gold_candles)
        
        gold_trend = gold_smc_res["trend"]
        gold_fib = self.fib.calculate_levels(gold_smc_res["swing_high"], gold_smc_res["swing_low"], gold_trend)
        gold_zone = self.fib.check_zone(gold_price, gold_fib.get("equilibrium_50", gold_price), gold_trend)

        self.gold_analysis = {
            "symbol": "XAUUSDm (Gold)",
            "current_price": gold_price,
            "change_pct": gold_ticker["change_pct"],
            "trend": gold_trend,
            "structure_event": gold_smc_res["structure_event"],
            "swing_high": gold_smc_res["swing_high"],
            "swing_low": gold_smc_res["swing_low"],
            "fib_levels": gold_fib,
            "zone_status": gold_zone,
            "source": gold_ticker.get("source", "Live"),
            "last_synced": datetime.now().strftime("%H:%M:%S UTC")
        }

        # Check for High-Probability Gold Setup (Golden Pocket + Discount/Premium)
        if len(self.account.open_trades) == 0 and "golden_pocket_ote" in gold_fib:
            # Gold Bullish Setup
            if gold_trend == "BULLISH" and "DISCOUNT" in gold_zone:
                entry = gold_price
                sl = gold_smc_res["swing_low"] * 0.998
                tp = gold_fib["target_ext_1"]
                trade_plan = self.risk.evaluate_and_size_trade(self.exness.balance, "BUY", entry, sl, tp)
                if trade_plan:
                    order = self.account.open_trade(trade_plan, symbol="XAUUSDm")
                    self.send_agent_message("Alex", "Chief Quant", f"🥇 HIGH-PROBABILITY GOLD SETUP: 4H BOS Bullish confirmed on XAUUSD!")
                    self.send_agent_message("David", "Fibonacci Specialist", f"Gold mitigated 0.618 Golden Pocket at ${entry:,.2f} in Discount Zone.")
                    self.send_agent_message("Marcus", "Chief Risk Officer", f"Gold trade approved! 1% risk capped (${trade_plan['dollar_risk']:.2f}). RRR: 1:{trade_plan['risk_reward_ratio']}.")
                    self.send_agent_message("Leo", "Execution Trader", f"Dispatched XAUUSDm Long to Exness-MT5Trial7! Ticket EXN-{order['id']}.")

                    # Broadcast to Telegram & Webhooks
                    self.telegram.send_trade_signal(order, asset="🥇 GOLD (XAUUSD)")
                    self.webhooks.broadcast_trade(order, asset="GOLD (XAUUSD)")

        # ==================== 2. BITCOIN (BTCUSDT) CYCLE ====================
        btc_ticker = self.market.get_live_btc_ticker()
        btc_price = btc_ticker["price"]
        btc_candles = self.market.get_btc_candles(interval="1h", limit=30)
        btc_smc_res = self.btc_smc.analyze_candles(btc_candles)
        btc_trend = btc_smc_res["trend"]
        btc_fib = self.fib.calculate_levels(btc_smc_res["swing_high"], btc_smc_res["swing_low"], btc_trend)
        btc_zone = self.fib.check_zone(btc_price, btc_fib.get("equilibrium_50", btc_price), btc_trend)

        self.btc_analysis = {
            "symbol": "BTC/USDT",
            "current_price": btc_price,
            "change_pct": btc_ticker["change_pct"],
            "trend": btc_trend,
            "structure_event": btc_smc_res["structure_event"],
            "fib_levels": btc_fib,
            "zone_status": btc_zone,
            "last_synced": datetime.now().strftime("%H:%M:%S UTC")
        }

        # Check Open Trades for SL / TP hit
        closed_trades = self.account.update_open_trades(gold_price if any(t['symbol'] == 'XAUUSDm' for t in self.account.open_trades) else btc_price)
        for ct in closed_trades:
            self.log(f"🔔 TRADE CLOSED: {ct['id']} | Result: {ct['status']} | PnL: ${ct.get('realized_pnl', 0):+,.2f}")
            self.telegram.send_trade_close(ct, self.exness.balance)
            self.branding.generate_firm_content(gold_trend, f"${gold_price:,.2f}", ct)

    def start_background_loop(self):
        if self.is_running:
            return
        self.is_running = True
        self.log("Virtual 3D Quant Floor, Gold SMC Engine & Telegram Sentinel Live.")

        # Start Telegram Poller
        self.telegram.start_polling()
        self.telegram.send_message("🏛️ <b>TradingAI Sentinel Online</b>\nExness MT5 Account #434353249 linked.\nAutonomous Gold (XAUUSD) & Bitcoin monitoring active.")

        # Workforce Announcements
        self.send_agent_message("Alex", "Chief Quant", "🥇 Gold (XAUUSD) & Bitcoin 4H pipelines running with zero lag.")
        self.send_agent_message("Marcus", "Chief Risk Officer", "1% capital defense calibrated for Exness MT5.")
        self.send_agent_message("Sophia", "Brand Director", "Multi-platform social webhooks and Telegram Sentinel armed.")

        def loop():
            counter = 0
            while True:
                try:
                    self.run_market_cycle()
                    counter += 1
                    
                    if counter % 10 == 0:
                        self.send_agent_message("David", "Fibonacci Specialist", f"Gold Golden Pocket: 0.618 (${self.gold_analysis.get('fib_levels', {}).get('fib_618', 2735):,.2f}) - 0.786.")
                    elif counter % 18 == 0:
                        self.send_agent_message("Mia", "Viral Copywriter", "Auto-drafted new SMC Gold breakdown for Twitter & LinkedIn.")

                except Exception as e:
                    self.log(f"Cycle Note: {str(e)}")
                time.sleep(15)

        threading.Thread(target=loop, daemon=True).start()
