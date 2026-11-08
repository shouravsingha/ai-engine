"""
Master Orchestrator
Connects Market Stream, SMC Engine, Fibonacci Engine, Risk Manager, Demo Desk, Exness Bridge, and Agency Engine.
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
from app.agency.social_engine import SocialEngine
from app.agency.lead_manager import LeadManager

class MasterOrchestrator:
    def __init__(self):
        self.market = MarketStream(symbol="BTCUSDT")
        self.smc = SMCEngine()
        self.fib = FibonacciEngine()
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.5)
        self.account = DemoAccount(initial_capital=50000.0)
        self.exness = ExnessBridge()
        self.social = SocialEngine()
        self.leads = LeadManager()
        
        self.system_logs: List[str] = []
        self.last_analysis: Dict[str, Any] = {}
        self.is_running = False

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
            if self.exness.connected:
                self.exness.balance = self.account.balance
                self.exness.equity = self.account.equity

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

        # 4. Check for High-Probability Setup (Golden Pocket + Discount + Trend Aligned)
        if len(self.account.open_trades) == 0 and "golden_pocket_ote" in fib_res:
            ote = fib_res["golden_pocket_ote"]
            
            # Bullish Trend setup
            if trend == "BULLISH" and "DISCOUNT" in zone_status:
                entry = current_price
                sl = swing_l * 0.998 # Invalidation just below swing low
                tp = fib_res["target_ext_1"] # Minimum 1st extension target
                
                trade_plan = self.risk.evaluate_and_size_trade(
                    account_balance=self.account.balance,
                    side="BUY",
                    entry_price=entry,
                    stop_loss=sl,
                    take_profit=tp
                )
                if trade_plan:
                    order = self.account.open_trade(trade_plan, symbol=ticker["symbol"])
                    self.log(f"🚀 SMC LONG EXECUTED: {order['id']} at ${entry:,.2f} | SL: ${sl:,.2f} | TP: ${tp:,.2f} | RRR: 1:{trade_plan['risk_reward_ratio']} | Risk: ${trade_plan['dollar_risk']}")
                    
                    if self.exness.connected:
                        ex_res = self.exness.sync_trade_execution(order)
                        self.log(f"🔗 EXNESS SYNC: {ex_res['message']}")

            # Bearish Trend setup
            elif trend == "BEARISH" and "PREMIUM" in zone_status:
                entry = current_price
                sl = swing_h * 1.002 # Invalidation just above swing high
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
                    self.log(f"🩸 SMC SHORT EXECUTED: {order['id']} at ${entry:,.2f} | SL: ${sl:,.2f} | TP: ${tp:,.2f} | RRR: 1:{trade_plan['risk_reward_ratio']} | Risk: ${trade_plan['dollar_risk']}")
                    
                    if self.exness.connected:
                        ex_res = self.exness.sync_trade_execution(order)
                        self.log(f"🔗 EXNESS SYNC: {ex_res['message']}")

    def start_background_loop(self):
        """Starts 24/7 autonomous loop."""
        if self.is_running:
            return
        self.is_running = True
        self.log("Institutional SMC Quant Engine, Exness Bridge & Agency Desk Started 24/7.")

        self.social.generate_content("BULLISH", "$65,000")

        def loop():
            counter = 0
            while True:
                try:
                    self.run_trading_cycle()
                    counter += 1
                    
                    if counter % 45 == 0:
                        trend = self.last_analysis.get("trend", "BULLISH")
                        price = f"${self.last_analysis.get('current_price', 0):,.2f}"
                        post = self.social.generate_content(trend, price)
                        self.log(f"📢 AI Social Content Published for: {post['platform']}")

                except Exception as e:
                    self.log(f"Worker Notice: {str(e)}")
                    
                time.sleep(20)

        threading.Thread(target=loop, daemon=True).start()
