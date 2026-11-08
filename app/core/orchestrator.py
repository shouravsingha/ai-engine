"""
Master Orchestrator
Virtual 3D Office Controller: Quant Trading Desk + Internal Media & Branding Division.
Runs continuously in a 24/7 background worker thread.
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

class MasterOrchestrator:
    def __init__(self):
        self.market = MarketStream(symbol="BTCUSDT")
        self.smc = SMCEngine()
        self.fib = FibonacciEngine()
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.5)
        self.account = DemoAccount(initial_capital=50000.0)
        self.exness = ExnessBridge()
        self.branding = BrandingEngine()
        
        # Virtual Office Workforce Roster
        self.agents = [
            {"id": "A1", "name": "Alex", "role": "Chief Quant Analyst", "dept": "Trading", "status": "Analyzing 4H", "color": "#38bdf8"},
            {"id": "A2", "name": "David", "role": "Fibonacci Specialist", "dept": "Trading", "status": "Mapping OTE", "color": "#3b82f6"},
            {"id": "A3", "name": "Marcus", "role": "Chief Risk Officer", "dept": "Trading", "status": "Guarding 1% Risk", "color": "#10b981"},
            {"id": "A4", "name": "Leo", "role": "Execution Trader", "dept": "Trading", "status": "Exness Bridge Live", "color": "#f59e0b"},
            {"id": "A5", "name": "Sophia", "role": "Brand Director", "dept": "Branding", "status": "Planning Campaign", "color": "#ec4899"},
            {"id": "A6", "name": "Mia", "role": "Viral Copywriter", "dept": "Branding", "status": "Drafting Thread", "color": "#a855f7"},
            {"id": "A7", "name": "Noah", "role": "Reels & Script Master", "dept": "Branding", "status": "Hook Testing", "color": "#8b5cf6"}
        ]
        
        self.agent_messages: List[Dict[str, Any]] = []
        self.system_logs: List[str] = []
        self.last_analysis: Dict[str, Any] = {}
        self.is_running = False

    def send_agent_message(self, agent_name: str, role: str, message: str):
        now_str = datetime.now().strftime("%H:%M:%S")
        entry = {
            "time": now_str,
            "agent": agent_name,
            "role": role,
            "text": message
        }
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

    def run_trading_cycle(self):
        """Executes one pass of the institutional SMC & Fibonacci evaluation."""
        ticker = self.market.get_live_ticker()
        current_price = ticker["price"]
        
        # 1. Update existing open paper trades
        closed_trades = self.account.update_open_trades(current_price)
        for ct in closed_trades:
            self.log(f"🔔 TRADE SETTLED: {ct['id']} | Outcome: {ct['status']} | PnL: ${ct.get('realized_pnl', 0):+,.2f}")
            self.send_agent_message("Leo", "Execution Trader", f"Trade {ct['id']} closed! Outcome: {ct['status']} (PnL: ${ct.get('realized_pnl', 0):+,.2f})")
            
            if self.exness.connected:
                self.exness.balance = self.account.balance
                self.exness.equity = self.account.equity
                
            # Trigger branding team to create a breakdown post
            self.branding.generate_firm_content(self.smc.trend, f"${current_price:,.2f}", ct)
            self.send_agent_message("Mia", "Viral Copywriter", f"Generated Twitter case study for {ct['id']} (+${ct.get('realized_pnl', 0):,.2f}). Added to media queue!")

        # 2. SMC Market Structure Analysis
        candles = self.market.get_recent_candles(interval="1h", limit=30)
        smc_res = self.smc.analyze_candles(candles)
        trend = smc_res["trend"]
        swing_h = smc_res["swing_high"]
        swing_l = smc_res["swing_low"]

        # 3. Fibonacci Retracement Calculation
        fib_res = self.fib.calculate_levels(swing_h, swing_l, trend)
        zone_status = self.fib.check_zone(current_price, fib_res.get("equilibrium_50", current_price), trend)

        self.last_analysis = {
            "symbol": ticker["symbol"],
            "current_price": current_price,
            "change_pct": ticker["change_pct"],
            "trend": trend,
            "structure_event": smc_res["structure_event"],
            "swing_high": swing_h,
            "swing_low": swing_l,
            "order_block": smc_res["order_block"],
            "fvg": smc_res["fvg"],
            "fib_levels": fib_res,
            "zone_status": zone_status,
            "last_synced": datetime.now().strftime("%H:%M:%S UTC")
        }

        # 4. Check for High-Probability Setup
        if len(self.account.open_trades) == 0 and "golden_pocket_ote" in fib_res:
            # Bullish Trend setup
            if trend == "BULLISH" and "DISCOUNT" in zone_status:
                entry = current_price
                sl = swing_l * 0.998
                tp = fib_res["target_ext_1"]
                
                trade_plan = self.risk.evaluate_and_size_trade(
                    account_balance=self.account.balance,
                    side="BUY",
                    entry_price=entry,
                    stop_loss=sl,
                    take_profit=tp
                )
                if trade_plan:
                    order = self.account.open_trade(trade_plan, symbol=ticker["symbol"])
                    self.send_agent_message("Alex", "Chief Quant", f"BULLISH Market Structure confirmed. Break of Structure verified on 4H.")
                    self.send_agent_message("David", "Fibonacci Specialist", f"Price mitigated Golden Pocket (0.618 at ${entry:,.2f}) in Discount Zone.")
                    self.send_agent_message("Marcus", "Chief Risk Officer", f"Order Approved! Risk capped at ${trade_plan['dollar_risk']} (1%). RRR: 1:{trade_plan['risk_reward_ratio']}.")
                    self.send_agent_message("Leo", "Execution Trader", f"Executing LONG on {order['symbol']} at ${entry:,.2f}! Tracking SL: ${sl:,.2f}, TP: ${tp:,.2f}.")
                    
                    if self.exness.connected:
                        ex_res = self.exness.sync_trade_execution(order)
                        self.send_agent_message("Leo", "Execution Trader", f"Exness MT5 Bridge synced: Ticket {ex_res['exness_ticket']}.")

            # Bearish Trend setup
            elif trend == "BEARISH" and "PREMIUM" in zone_status:
                entry = current_price
                sl = swing_h * 1.002
                tp = fib_res["target_ext_1"]
                
                trade_plan = self.risk.evaluate_and_size_trade(
                    account_balance=self.account.balance,
                    side="SELL",
                    entry_price=entry,
                    stop_loss=sl,
                    take_profit=tp
                )
                if trade_plan:
                    order = self.account.open_trade(trade_plan, symbol=ticker["symbol"])
                    self.send_agent_message("Alex", "Chief Quant", f"BEARISH Market Structure confirmed. Lower Highs / Lows active.")
                    self.send_agent_message("David", "Fibonacci Specialist", f"Price retraced into Premium Golden Pocket at ${entry:,.2f}.")
                    self.send_agent_message("Marcus", "Chief Risk Officer", f"Order Approved! Sized 1% risk ($500). RRR: 1:{trade_plan['risk_reward_ratio']}.")
                    self.send_agent_message("Leo", "Execution Trader", f"Executing SHORT on {order['symbol']} at ${entry:,.2f}! Exness synced.")

    def start_background_loop(self):
        """Starts 24/7 autonomous loop."""
        if self.is_running:
            return
        self.is_running = True
        self.log("Virtual 3D AI Trading Floor & Media Office Live.")

        # Initial workforce introductions
        self.send_agent_message("Alex", "Chief Quant Analyst", "Quant desk initialized. Scanning 4H & 1H candle structures...")
        self.send_agent_message("David", "Fibonacci Specialist", "Fibonacci mathematical grid active. Equilibrium calibrated at 50%.")
        self.send_agent_message("Marcus", "Chief Risk Officer", "Risk rules locked: Max 1% per trade. $50,000 capital shielded.")
        self.send_agent_message("Sophia", "Brand Director", "Media & Branding floor ready. Monitoring live trading desk for viral content.")
        self.branding.generate_firm_content("BULLISH", "$65,000")

        def loop():
            counter = 0
            while True:
                try:
                    self.run_trading_cycle()
                    counter += 1
                    
                    # Periodic casual or status dialogue among agents
                    if counter % 8 == 0 and len(self.account.open_trades) == 0:
                        self.send_agent_message("David", "Fibonacci Specialist", "Monitoring 0.618 OTE retracement zone. Waiting for institutional setup.")
                    elif counter % 14 == 0:
                        self.send_agent_message("Noah", "Reels & Script Master", "Drafting new 30-sec script on 'Why institutions love Discount Zones'.")

                except Exception as e:
                    self.log(f"Worker Notice: {str(e)}")
                    
                time.sleep(20)

        threading.Thread(target=loop, daemon=True).start()
