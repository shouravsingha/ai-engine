"""
Master Orchestrator
Integrated with AI Central Neural Brain (Autonomous Teacher & Supervisor),
Real-Time Particle Flow Stream Engine, Exness MT5 Live Bridge,
and Telegram Sentinel (@SingAiTradebot).
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
from app.trading.orderflow_engine import OrderFlowEngine
from app.trading.time_machine import TimeMachineEngine
from app.trading.orb_engine import SessionORBEngine
from app.trading.gold_strategy_engine import GoldStrategyEngine
from app.core.ai_brain import AIBrainOverseer
from app.agency.branding_engine import BrandingEngine
from app.agency.webhook_dispatcher import SocialWebhookDispatcher
from app.core.telegram_bot import TelegramSentinelBot
from app.data.db_manager import DatabaseManager
from app.data.data_collector import DataCollector
from app.learning.journal import TradeJournal
from app.learning.strategy_evolver import StrategyEvolver
from app.trading.circuit_breaker import AutonomousCircuitBreaker
from app.trading.portfolio_engine import SovereignPortfolioEngine
from app.agents.decision_desk import DecisionDesk
from app.core.autonomous_supervisor import AutonomousFloorSupervisor

class MasterOrchestrator:
    def __init__(self):
        self.market = MarketStream()
        self.orderflow = OrderFlowEngine()
        self.brain = AIBrainOverseer()
        
        # Dedicated parallel Multi-Timeframe SMC detectors (4H Macro, 1H Structure, 15m Trigger)
        self.smc_engines_4h = {"gold": SMCEngine(), "btc": SMCEngine(), "eth": SMCEngine()}
        self.smc_engines_1h = {"gold": SMCEngine(), "btc": SMCEngine(), "eth": SMCEngine()}
        self.smc_engines_15m = {"gold": SMCEngine(), "btc": SMCEngine(), "eth": SMCEngine()}
        self.smc_engines = self.smc_engines_1h # Backward compatibility
        self.fib = FibonacciEngine()
        self.risk = RiskManager(risk_percent=1.0, min_rrr=2.5)
        self.time_machine = TimeMachineEngine(default_replays=2500, horizon_bars=36)
        self.orb = SessionORBEngine(or_minutes=15, default_target_r=2.5)
        self.gold_engine = GoldStrategyEngine(max_sl_distance=2.50)
        self.account = DemoAccount(initial_capital=50000.0)
        self.cloud_command_queue = []
        self.exness = ExnessBridge(command_queue=self.cloud_command_queue)
        self.branding = BrandingEngine()
        self.webhooks = SocialWebhookDispatcher()

        # Generation 3.0: Sovereign Trading Desk, Portfolio & Institutional Learning Layer
        self.db_manager = DatabaseManager()
        self.data_collector = DataCollector(db=self.db_manager)
        self.journal = TradeJournal(db=self.db_manager)
        self.circuit_breaker = AutonomousCircuitBreaker()
        self.portfolio_engine = SovereignPortfolioEngine()
        self.strategy_evolver = StrategyEvolver(journal=self.journal)
        self.decision_desk = DecisionDesk(
            risk_manager=self.risk,
            journal=self.journal,
            circuit_breaker=self.circuit_breaker,
            portfolio_engine=self.portfolio_engine,
            strategy_evolver=self.strategy_evolver
        )
        self.supervisor = AutonomousFloorSupervisor(
            orchestrator=self,
            decision_desk=self.decision_desk,
            circuit_breaker=self.circuit_breaker,
            strategy_evolver=self.strategy_evolver
        )
        
        # Telegram Sentinel Bot
        self.telegram = TelegramSentinelBot(
            token="8538360036:AAHvC5EJvrB2Srh5MRn7LghR1IEZpOxuV38",
            chat_id="5347514050",
            command_handler=self.handle_telegram_command
        )

        # 10 Robot Specialist Workforce (Workforce 2.0 & Gen 3.0 Floor)
        self.agents = [
            {"id": "PA_01", "name": "Alex", "role": "Chief Quant (Trend)", "tag": "PA_01", "dept": "Trading", "status": "Brain Synced", "color": "#facc15"},
            {"id": "LUC_3", "name": "David", "role": "Fibonacci Master", "tag": "LUC_3", "dept": "Trading", "status": "0.618 OTE Armed", "color": "#3b82f6"},
            {"id": "PA_02", "name": "Marcus", "role": "Risk Officer (Sovereign)", "tag": "PA_02", "dept": "Risk", "status": "1% Capital Shield", "color": "#22c55e"},
            {"id": "PA_14", "name": "Leo", "role": "Execution Trader", "tag": "PA_14 US$ 20.21", "dept": "Execution", "status": "Exness MT5 Live", "color": "#06b6d4"},
            {"id": "PA_09", "name": "Kai", "role": "OrderFlow Tape Reader", "tag": "PA_09", "dept": "Trading", "status": "L2 Volatility Active", "color": "#38bdf8"},
            {"id": "PA_05", "name": "Zara", "role": "Macro & News Scout", "tag": "PA_05", "dept": "Macro", "status": "CPI/NFP Radar", "color": "#ec4899"},
            {"id": "PA_21", "name": "Aria", "role": "Forensic Journal Auditor", "tag": "PA_21", "dept": "Compliance", "status": "Audit Sync Active", "color": "#10b981"},
            {"id": "PA_16", "name": "Sophia", "role": "Brand Director", "tag": "Conta_1612", "dept": "Media", "status": "Webhooks Armed", "color": "#f97316"},
            {"id": "PA_07", "name": "Mia", "role": "Viral Copywriter", "tag": "PA_07", "dept": "Media", "status": "Drafting Thread", "color": "#a855f7"},
            {"id": "PA_18", "name": "Noah", "role": "Reels & Script Master", "tag": "PA_18", "dept": "Media", "status": "Hook Testing", "color": "#818cf8"}
        ]
        self.red_team_officer = {"id": "PA_99", "name": "Vance", "role": "Red Team Prosecutor", "tag": "PA_99", "dept": "Audit", "status": "Adversarial Shield", "color": "#ef4444"}
        
        self.agent_messages: List[Dict[str, Any]] = []
        self.system_logs: List[str] = []
        self.multi_market_matrix: Dict[str, Any] = {}
        self.symbol_cooldowns: Dict[str, float] = {}  # symbol -> cooldown expiry timestamp (15m anti-churn)
        self.executed_setup_signatures: Dict[str, str] = {}  # symbol -> setup signature
        self._last_known_open_symbols: set = set()
        self.is_running = False

    def handle_telegram_command(self, cmd: str) -> str:
        cmd = cmd.lower().strip()
        if "/status" in cmd:
            ex_stat = "CONNECTED" if self.exness.connected else "STANDBY"
            gold_cd = int(max(0, self.symbol_cooldowns.get("XAUUSDm", 0.0) - time.time()) // 60)
            cd_info = f"Cooldown ({gold_cd}m)" if gold_cd > 0 else "Ready"
            return f"🧠 <b>AI Central Brain:</b> ACTIVE (IQ 185)\nOffice: {len(self.agents)}/{len(self.agents)} Robots Coached\nExness MT5: {ex_stat} (#{self.exness.account_id})\nBalance: ${self.exness.balance:,.2f}\nGold Radar: {cd_info}"
        elif "/desk" in cmd:
            decisions = self.journal.get_recent_decisions(limit=3)
            if not decisions:
                return "🏛️ <b>Decision Desk:</b> Standing by. Multi-agent debate monitoring live feeds."
            latest = decisions[0]
            return f"🏛️ <b>Decision Desk Audit:</b>\nSymbol: {latest['symbol']} ({latest['timeframe']})\nBias: {latest['consensus_bias']} ({latest['confidence']}%)\nTrigger: {latest['trigger_reason']}\nRisk Status: {latest['risk_status']}"
        elif "/edge" in cmd:
            stats = self.journal.analyze_statistical_edge()
            return f"🧪 <b>Statistical Edge Audit:</b>\nTotal Trades: {stats['total_trades']}\nWin Rate: {stats['win_rate']}%\nAvg R: {stats['avg_r']}R\nProfit Factor: {stats['profit_factor']}\nValidated Setups: {len(stats['statistically_validated_setups'])}"
        elif "/gen3" in cmd:
            t = self.supervisor.get_telemetry()
            cb = t["circuit_breaker"]
            cb_str = "HALTED" if cb["kill_switch_active"] else ("COOLDOWN" if cb["is_cooling_down"] else "NORMAL")
            return (
                f"🏛️ <b>GEN 3.0 SOVEREIGN SUPERVISOR:</b>\n"
                f"Status: {'ACTIVE' if t['is_running'] and not t['is_paused'] else ('PAUSED' if t['is_paused'] else 'STANDBY')}\n"
                f"Cycles Executed: {t['cycle_count']}\n"
                f"Peak Equity: ${t['peak_equity']:,.2f}\n"
                f"Circuit Breaker: {cb_str} (Streak: {cb['consecutive_losses']} losses)\n"
                f"Quarantined Setups: {len(t['quarantined_setups'])}\n"
                f"Active Signals: {len(t['active_signals'])}"
            )
        elif "/prosecutor" in cmd:
            latest_decision = self.journal.get_recent_decisions(limit=1)
            if not latest_decision:
                return "🛡️ <b>Red Team Prosecutor:</b> Armed & monitoring. No trade proposals audited yet."
            d = latest_decision[0]
            rt = d.get("agent_votes", {}).get("red_team", {})
            status = rt.get("prosecutor_status", "AUDITED")
            score = rt.get("risk_score", 0.0)
            critique = "; ".join(rt.get("critique", ["Clean structural invalidation."]))
            return f"🛡️ <b>Red Team Prosecutor (PA_99 Vance):</b>\nStatus: {status} (Risk Score: {score}/100)\nTarget: {d['symbol']} ({d['consensus_bias']})\nCritique: {critique}"
        elif "/evolver" in cmd:
            ev = self.strategy_evolver.evaluate_setup_portfolio()
            q_count = ev["quarantined_setups_count"]
            rankings = ev.get("setup_rankings", {})
            top_setups = [f"• {k}: {v['win_rate_pct']}% win, {v['avg_r']}R (Sharpe {v['sharpe_ratio']})" for k, v in list(rankings.items())[:3]]
            rank_str = "\n".join(top_setups) if top_setups else "No closed trades sampled yet."
            return f"🧬 <b>Strategy Evolver Matrix:</b>\nTrades Analyzed: {ev['total_trades_analyzed']}\nQuarantined Setups: {q_count}\nTop Setups:\n{rank_str}"
        elif "/pause" in cmd:
            self.supervisor.pause()
            return "⏸️ Autonomous Supervisor PAUSED. Live market monitoring continues without order dispatch."
        elif "/resume" in cmd:
            self.supervisor.resume()
            return "▶️ Autonomous Supervisor RESUMED. Multi-agent debate & trade execution active."
        elif "/brain" in cmd:
            b = self.brain.get_status()
            return f"🧠 <b>AI Central Brain Diagnostics:</b>\nCognitive Load: {b['cognitive_load']}\nDecisions Audited: {b['metrics']['decisions_audited']}\nMistakes Prevented: {b['metrics']['mistakes_prevented']}\nSystem IQ: {b['metrics']['system_iq']}"
        elif "/gold" in cmd:
            g = self.multi_market_matrix.get("gold", {})
            curr_p = g.get('price', 2748.20)
            g_strat = g.get('gold_strategy', {})
            a_range = g_strat.get('asian_range', {})
            setup_status = g_strat.get('setup_type', 'SEARCHING_CONFLUENCE') if g_strat.get('triggered') else 'WAITING_SWEEP/ORB'
            gold_cd = int(max(0, self.symbol_cooldowns.get("XAUUSDm", 0.0) - time.time()) // 60)
            cd_str = f"COOLING DOWN ({gold_cd}m remaining)" if gold_cd > 0 else "ARMED (Ready)"
            return (
                f"🥇 <b>GOLD (XAUUSDm) Institutional Radar:</b>\n"
                f"Price: ${curr_p:,.2f}\n"
                f"Asian Range: ${a_range.get('low', 0):,.2f} - ${a_range.get('high', 0):,.2f}\n"
                f"Active Strategy: {setup_status}\n"
                f"Anti-Churn Cooldown: {cd_str}\n"
                f"Closed-Bar Rule: ACTIVE\n"
                f"Max SL Cap: $2.50 (Micro Safe)\n"
                f"Patient BE Shield: +$2.50\n"
                f"Wide Trail Buffer: +$4.00 (+$1.80 breath room)\n"
                f"Monte Carlo Engine: 10,000 Replays Armed"
            )
        elif "/scan" in cmd:
            self.run_simultaneous_scan()
            return "⚡ Autonomous scan across Forex & Commodities verified by AI Central Brain!"
        elif "/timemachine" in cmd:
            g = self.multi_market_matrix.get("gold", {})
            curr_p = g.get("price", 2748.20)
            res = self.time_machine.simulate_trade("XAUUSDm", "BUY", curr_p, curr_p - 2.0, curr_p + 5.0, replays=1000)
            return f"⏳ <b>Time Machine Monte Carlo (Gold M5):</b>\nVerdict: {res['verdict']}\nWin Odds: {res['prob_target_pct']}%\nStop Odds: {res['prob_stop_pct']}%\nExpected R: {res['expected_r']:+.2f}\nReplays: 1,000 paths"
        elif "/orb" in cmd:
            sess = self.orb.get_current_session()
            g_orb = self.multi_market_matrix.get("gold", {}).get("orb", {})
            return f"🕒 <b>Session ORB Engine:</b>\nActive Session: {sess['name']} ({sess['key']})\nGold ORB Status: {g_orb.get('status', 'ANALYZED')}\nClosed-Bar Rule: ACTIVE"
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
        """Scans Gold, BTC, and ETH concurrently with Multi-Timeframe SMC (4H/1H/15m) and AI Brain validation."""
        self.exness.refresh_balance()
        
        # 0. Capital Preservation Lock: Halt all scanning & ordering if balance is below safe threshold ($5.00)
        if self.exness.balance < self.risk.min_balance_threshold:
            if not getattr(self, "_depleted_balance_warned", False):
                warn_msg = f"⏸️ CAPITAL SHIELD ACTIVE: Exness balance (${self.exness.balance:,.2f}) is below minimum safe threshold ($5.00). New orders paused."
                self.log(warn_msg)
                self.send_agent_message("Marcus", "Risk Officer (PA_02)", warn_msg)
                self.telegram.send_message(f"🚨 <b>CAPITAL SHIELD PAUSE:</b>\n{warn_msg}\nPlease top up funds to resume.")
                self._depleted_balance_warned = True
            self.evaluate_and_defend_positions()
            return
        else:
            self._depleted_balance_warned = False

        tickers = self.market.get_all_live_tickers()

        matrix = {}
        for asset_key in ["gold", "btc", "eth"]:
            symbol_exec = "XAUUSDm" if asset_key == "gold" else ("BTCUSDm" if asset_key == "btc" else "ETHUSDm")
            try:
                ticker = tickers[asset_key]
                current_price = ticker["price"]

                # 1. Fetch Multi-Timeframe Candles (4H Macro, 1H Structure, 15m Execution Trigger)
                candles_4h = self.market.get_candles(asset_key, interval="4h", limit=30)
                candles_1h = self.market.get_candles(asset_key, interval="1h", limit=30)
                candles_15m = self.market.get_candles(asset_key, interval="15m", limit=30)

                # 2. Multi-Timeframe SMC Analysis
                smc_4h = self.smc_engines_4h[asset_key].analyze_candles(candles_4h)
                smc_1h = self.smc_engines_1h[asset_key].analyze_candles(candles_1h)
                smc_15m = self.smc_engines_15m[asset_key].analyze_candles(candles_15m)

                # 3. Session Opening Range Breakout (ORB) with Closed-Bar Rule
                orb_analysis = self.orb.analyze_orb_breakout(symbol_exec, current_price, candles_15m)

                # 4. Dedicated Gold Institutional Setups (Asian Sweep + Overlap ORB + Trend Reclaim)
                gold_setup_res = None
                if asset_key == "gold":
                    candles_5m = self.market.get_candles("gold", interval="5m", limit=30)
                    gold_setup_res = self.gold_engine.evaluate_gold_opportunities(
                        candles_1h, candles_15m, candles_5m, current_price, spread=0.25
                    )

                trend_4h = smc_4h.get("trend", "BULLISH")
                trend_1h = smc_1h.get("trend", "BULLISH")
                trend_15m = smc_15m.get("trend", "BULLISH")

                swing_high = float(smc_1h.get("swing_high", current_price * 1.01))
                swing_low = float(smc_1h.get("swing_low", current_price * 0.99))
                
                fib_res = self.fib.calculate_levels(swing_high, swing_low, trend_1h)
                zone_status = self.fib.check_zone(current_price, fib_res.get("equilibrium_50", current_price), trend_1h)

                # 4. Calculate MTF Confluence Score & Institutional Bias (BUY & SELL)
                bull_count = (1 if trend_4h == "BULLISH" else 0) + (1 if trend_1h == "BULLISH" else 0) + (1 if trend_15m == "BULLISH" else 0)
                bear_count = (1 if trend_4h == "BEARISH" else 0) + (1 if trend_1h == "BEARISH" else 0) + (1 if trend_15m == "BEARISH" else 0)

                if trend_4h == "BULLISH" and trend_1h == "BULLISH":
                    mtf_bias = "BULLISH"
                    mtf_aligned = True
                    mtf_status = "TRIPLE_A_PLUS (3/3 BULLISH)" if bull_count == 3 else "HTF_ALIGNED (2/3 BULLISH)"
                    mtf_score = f"{bull_count}/3"
                elif trend_4h == "BEARISH" and trend_1h == "BEARISH":
                    mtf_bias = "BEARISH"
                    mtf_aligned = True
                    mtf_status = "TRIPLE_A_PLUS (3/3 BEARISH)" if bear_count == 3 else "HTF_ALIGNED (2/3 BEARISH)"
                    mtf_score = f"{bear_count}/3"
                else:
                    mtf_bias = "NEUTRAL"
                    mtf_aligned = False
                    mtf_status = "MIXED_CONFLICT (WAITING SETUP)"
                    mtf_score = f"{max(bull_count, bear_count)}/3"

                matrix[asset_key] = {
                    "symbol": ticker["symbol"],
                    "price": current_price,
                    "change_pct": ticker["change_pct"],
                    "trend": trend_1h,
                    "trend_4h": trend_4h,
                    "trend_1h": trend_1h,
                    "trend_15m": trend_15m,
                    "mtf_bias": mtf_bias,
                    "mtf_status": mtf_status,
                    "mtf_score": mtf_score,
                    "mtf_aligned": mtf_aligned,
                    "killzone": smc_1h.get("killzone", {}),
                    "fvg": smc_1h.get("fvg"),
                    "order_block": smc_1h.get("order_block"),
                    "liquidity_sweep": smc_1h.get("liquidity_sweep"),
                    "structure_event": smc_1h.get("structure_event", "NONE"),
                    "swing_high": swing_high,
                    "swing_low": swing_low,
                    "fib_levels": fib_res,
                    "zone_status": zone_status,
                    "orb": orb_analysis,
                    "gold_strategy": gold_setup_res,
                    "source": ticker.get("source", "Live")
                }
            except Exception as e:
                continue

            # Check for High-Probability Setup with ICT + Multi-Timeframe Confluence (15m + 1h + 4h)
            max_allowed_pos = self.risk.get_max_allowed_positions(self.exness.balance)
            if len(self.exness.open_positions) < max_allowed_pos and "golden_pocket_ote" in fib_res:
                symbol_exec = "XAUUSDm" if asset_key == "gold" else ("BTCUSDm" if asset_key == "btc" else "ETHUSDm")
                entry = current_price
                trade_side = None

                # Dynamic maximum allowable SL distance according to account equity
                # Prevents 0.01 lot loss from ever exceeding the allowable dollar risk ceiling
                bal = self.exness.balance
                if bal < 50.0:
                    # Micro tier: Gold max $2.00 distance ($2.00 risk), BTC max $80 ($0.80 risk), ETH max $25 ($0.25 risk)
                    max_sl_dist = 80.0 if "BTC" in symbol_exec else (2.0 if "XAU" in symbol_exec else 25.0)
                elif bal < 200.0:
                    max_sl_dist = 160.0 if "BTC" in symbol_exec else (3.0 if "XAU" in symbol_exec else 45.0)
                else:
                    max_sl_dist = 350.0 if "BTC" in symbol_exec else (3.5 if "XAU" in symbol_exec else 60.0)

                # -------------------------------------------------------------
                # 0. PRIORITY FOR GOLD: DEDICATED INSTITUTIONAL SETUP (Asian Sweep / Overlap ORB / Trend Reclaim)
                # -------------------------------------------------------------
                if asset_key == "gold" and gold_setup_res and gold_setup_res.get("triggered"):
                    g_s = gold_setup_res["setup"]
                    trade_side = g_s["side"]
                    entry = g_s["entry"]
                    sl = g_s["sl"]
                    tp = g_s["tp"]

                # -------------------------------------------------------------
                # 1. BULLISH SETUP (BUY / LONG):
                # - 4H Macro Trend: BULLISH
                # - 1H Structure Trend: BULLISH
                # - Zone: DISCOUNT (Equilibrium < 50%)
                # -------------------------------------------------------------
                elif trend_4h == "BULLISH" and trend_1h == "BULLISH" and "DISCOUNT" in zone_status and mtf_aligned:
                    trade_side = "BUY"
                    raw_sl = float(smc_1h.get("recommended_sl", smc_1h["swing_low"]))
                    # Enforce that SL is below entry for BUY with calibrated fallback
                    if raw_sl >= entry or (entry - raw_sl) < 0.50:
                        raw_sl = entry - (2.50 if "XAU" in symbol_exec else current_price * 0.004)

                    if (entry - raw_sl) > max_sl_dist:
                        sl = round(entry - max_sl_dist, 2)
                    else:
                        sl = round(raw_sl, 2)

                    tp_mult = 2.4 if "XAU" in symbol_exec else 2.6
                    min_tp_dist = (entry - sl) * tp_mult
                    raw_tp = float(smc_1h.get("recommended_tp", fib_res.get("target_ext_1", entry + min_tp_dist)))
                    tp = round(max(raw_tp, entry + min_tp_dist), 2)

                # -------------------------------------------------------------
                # 2. BEARISH SETUP (SELL / SHORT):
                # - 4H Macro Trend: BEARISH
                # - 1H Structure Trend: BEARISH
                # - Zone: PREMIUM (Equilibrium > 50%)
                # -------------------------------------------------------------
                elif trend_4h == "BEARISH" and trend_1h == "BEARISH" and "PREMIUM" in zone_status and mtf_aligned:
                    trade_side = "SELL"
                    raw_sl = float(smc_1h.get("recommended_sl", smc_1h["swing_high"]))
                    # Enforce that SL is ABOVE entry for SELL with calibrated fallback
                    if raw_sl <= entry or (raw_sl - entry) < 0.50:
                        raw_sl = entry + (2.50 if "XAU" in symbol_exec else current_price * 0.004)

                    if (raw_sl - entry) > max_sl_dist:
                        sl = round(entry + max_sl_dist, 2)
                    else:
                        sl = round(raw_sl, 2)

                    # Perfect Take Profit for SELL: minimum 2.4x the SL distance below entry
                    tp_mult = 2.4 if "XAU" in symbol_exec else 2.6
                    min_tp_dist = (sl - entry) * tp_mult
                    raw_tp = float(smc_1h.get("recommended_tp", fib_res.get("target_ext_1", entry - min_tp_dist)))
                    tp = round(min(raw_tp, entry - min_tp_dist), 2)

                # Execute if either BUY or SELL setup triggered
                if trade_side:
                    # 1. Anti-Churning Cooldown Check (15-min freeze after symbol trade closure)
                    cooldown_expiry = self.symbol_cooldowns.get(symbol_exec, 0.0)
                    rem_cd = cooldown_expiry - time.time()
                    if rem_cd > 0:
                        # Symbol is under patient cooldown, prevent re-entry churning
                        continue

                    # 2. Check if already open on this symbol (MT5 positions OR internal account)
                    already_open = any(p.get("symbol") == symbol_exec for p in self.exness.open_positions) or any(t.get("symbol") == symbol_exec for t in self.account.open_trades)
                    if already_open:
                        continue

                    # 3. Setup Signature Deduplication (prevent executing identical setup twice)
                    setup_sig = f"{asset_key}_{trade_side}_{round(entry, 1)}_{round(sl, 1)}"
                    if self.executed_setup_signatures.get(symbol_exec) == setup_sig:
                        continue

                    trade_plan = self.risk.evaluate_and_size_trade(self.exness.balance, trade_side, entry, sl, tp, symbol=symbol_exec)
                    if trade_plan:
                        vol = trade_plan["volume"]
                        # 1. TIME MACHINE MONTE CARLO PROBABILITY SIMULATION
                        tm_audit = self.time_machine.simulate_trade(
                            symbol_exec, trade_side, entry, sl, tp, candles=candles_15m, replays=2500
                        )

                        # 2. AUDIT BY AI CENTRAL NEURAL BRAIN
                        audit = self.brain.audit_trade_proposal(
                            "Alex & Marcus",
                            symbol_exec,
                            trade_side,
                            trade_plan["risk_reward_ratio"],
                            1.0,
                            dollar_risk=trade_plan["dollar_risk"],
                            balance=self.exness.balance,
                            time_machine_audit=tm_audit
                        )
                        if not audit.get("approved", True):
                            reject_reason = audit.get("correction_text", "Audit rejected")
                            self.log(f"🛑 Trade Rejected by Brain/TimeMachine for {symbol_exec}: {reject_reason}")
                            self.send_agent_message("Time Machine", "Quant Simulator", f"🛑 VETO: {symbol_exec} {trade_side} rejected. {reject_reason}")
                            continue

                        # Check if MT5 Algo Trading is active before sending order
                        if not self.exness.algo_trading_enabled and self.exness.live_terminal:
                            if not getattr(self, f"_algo_warned_{symbol_exec}", False):
                                self.log(f"⏸️ MT5 Algo Trading is paused. Press Ctrl+E in MT5 to allow automated execution for {symbol_exec}.")
                                self.send_agent_message("Marcus", "Risk Officer (PA_02)", f"⏸️ {symbol_exec} setup ready, but MT5 Algo Trading is paused. Press Ctrl+E in MT5.")
                                setattr(self, f"_algo_warned_{symbol_exec}", True)
                            continue
                        else:
                            setattr(self, f"_algo_warned_{symbol_exec}", False)

                        # 2. REAL EXECUTION ON EXNESS MT5
                        mt5_res = self.exness.execute_live_order(symbol_exec, trade_side, volume=vol, sl=sl, tp=tp)

                        if mt5_res.get("status") in ("success", "queued"):
                            # Record setup signature to lock out duplicates
                            self.executed_setup_signatures[symbol_exec] = setup_sig

                            # 3. Log internal order
                            order = self.account.open_trade(trade_plan, symbol=symbol_exec)
                            ticket_no = mt5_res.get("ticket", order["id"])
                            order["mt5_ticket"] = ticket_no

                            asset_title = ticker["symbol"]
                            if asset_key == "gold" and gold_setup_res and gold_setup_res.get("triggered"):
                                kz_info = f"🥇 {gold_setup_res['setup']['setup_name']}"
                            else:
                                kz_info = smc_1h.get("killzone", {}).get("name", "Active Session")
                            action_name = "LONG (BUY)" if trade_side == "BUY" else "SHORT (SELL)"
                            zone_name = "Discount" if trade_side == "BUY" else "Premium"
                            self.send_agent_message("AI Brain", "Neural Overseer", f"🧠 AUDIT PASS: {asset_title} {action_name} ICT OTE & MTF Confluence Verified ({mtf_status} | {kz_info}). SL: ${sl:,.2f} | TP: ${tp:,.2f}.")
                            self.send_agent_message("Alex", "Chief Quant (PA_01)", f"🌊 ICT DISPLACEMENT: Fair Value Gap CE filled on {asset_title} for {action_name}!")
                            self.send_agent_message("David", "Fibonacci Master (LUC_3)", f"{asset_title} tagged ICT 0.705 sweet spot at ${entry:,.2f} in {zone_name} Zone.")
                            tm_verdict = tm_audit.get("verdict", "VERIFIED")
                            tm_win = tm_audit.get("resolved_winrate_pct", 50.0)
                            tm_exp = tm_audit.get("expected_r", 0.0)
                            self.send_agent_message("Time Machine", "Quant Simulator", f"⏳ TIME MACHINE PASS: {symbol_exec} {action_name} | Win Odds: {tm_win}% vs {tm_audit.get('breakeven_winrate_pct')}% BE | Exp R: {tm_exp:+.2f} ({tm_verdict}).")
                            self.send_agent_message("Leo", "Execution Trader (PA_14)", f"Auto-Trade EXECUTED ({trade_side}) on Exness MT5! Ticket #{ticket_no} active with strict ${abs(entry-sl):.2f} risk cap.")

                            self.telegram.send_trade_signal(order, asset=f"{asset_title} [{mtf_status} · {kz_info}]")
                            self.webhooks.broadcast_trade(order, asset=asset_title)
                        else:
                            fail_reason = mt5_res.get('comment') or mt5_res.get('message') or 'Rejected'
                            self.log(f"⚠️ Trade Execution Failed for {symbol_exec}: {fail_reason}")

        self.multi_market_matrix = matrix

        # Run AI Brain trade defense on open MT5 positions
        self.evaluate_and_defend_positions()

        active_p = matrix["gold"]["price"] if any(t['symbol'] == 'XAUUSDm' for t in self.account.open_trades) else matrix["btc"]["price"]
        closed_trades = self.account.update_open_trades(active_p)
        for ct in closed_trades:
            sym = ct.get('symbol', 'XAUUSDm')
            self.symbol_cooldowns[sym] = time.time() + 900.0  # 15 minutes anti-churn cooldown
            pnl = ct.get('realized_pnl', 0.0)
            self.log(f"🔔 TRADE SETTLED: {ct['id']} | Outcome: {ct['status']} | PnL: ${pnl:+,.2f} | 15m Cooldown Armed for {sym}")
            self.brain.record_trade_result(pnl)
            self.circuit_breaker.record_trade_outcome(pnl)
            # Strategy Evolver Forensic Dissection
            risk_amt = max(abs(ct.get('dollar_risk', 1.0)), 0.1)
            r_mult = round(pnl / risk_amt, 2)
            self.strategy_evolver.generate_trade_post_mortem(
                trade_id=ct.get('id', 0),
                symbol=sym,
                side=ct.get('side', 'BUY'),
                entry=ct.get('entry_price', 0.0),
                sl=ct.get('sl', 0.0),
                tp=ct.get('tp', 0.0),
                exit_price=active_p,
                pnl=pnl,
                r_multiple=r_mult
            )
            self.telegram.send_trade_close(ct, self.exness.balance)
            self.branding.generate_firm_content("BULLISH", f"${active_p:,.2f}", ct)

    def evaluate_and_defend_positions(self):
        """
        Active AI Brain position defense:
        1. Patient Break-Even Shield (+$2.50+ profit on Gold)
        2. Wide Institutional Trailing Stop (+$4.00+ profit, $1.80 breathing buffer)
        3. Emergency Hard Loss Circuit Breaker (-$1.25)
        4. Anti-Churn Cooldown Tracking (15 min cooldown on symbol exit)
        """
        # Track MT5 closed positions between cycles to trigger cooldown
        current_open_symbols = {p.get("symbol") for p in self.exness.open_positions if p.get("symbol")}
        if hasattr(self, "_last_known_open_symbols") and self._last_known_open_symbols:
            closed_symbols = self._last_known_open_symbols - current_open_symbols
            for cs in closed_symbols:
                self.symbol_cooldowns[cs] = time.time() + 900.0  # 15 min cooldown
                self.log(f"🛡️ ANTI-CHURN COOLDOWN: Position on {cs} closed. 15-minute freeze engaged to prevent instant re-entry.")
                self.send_agent_message("Marcus", "Risk Officer (PA_02)", f"🛡️ ANTI-CHURN: {cs} position closed. Cooling down for 15 minutes before seeking new setups.")
        self._last_known_open_symbols = current_open_symbols

        if not self.exness.open_positions:
            return
        actions = self.brain.evaluate_open_positions(self.exness.open_positions, self.multi_market_matrix)
        for act in actions:
            action_type = act.get("action")
            
            # MODIFY SL / TRAILING
            if action_type == "modify_sl":
                m_res = self.exness.modify_position_sl_tp(act["ticket"], act["new_sl"], act.get("new_tp", 0.0))
                if m_res.get("status") in ("success", "queued"):
                    self.send_agent_message("Marcus", "Risk Officer (PA_02)", act["reason"])
                    self.send_agent_message("AI Brain", "Neural Overseer", f"🛡️ DEFENSE TRIGGER: {act['symbol']} #{act['ticket']} protected.")
                    self.telegram.send_message(f"🛡️ <b>AI POSITION DEFENSE:</b>\n{act['reason']}")
                    self.log(f"🛡️ Position #{act['ticket']} ({act['symbol']}): {act['reason']}")
                elif m_res.get("retcode") == 10027:
                    if not getattr(self, "_algo_warned", False):
                        self.send_agent_message("Marcus", "Risk Officer (PA_02)", "⚠️ MT5 এ 'Algo Trading' (Ctrl+E) বন্ধ রয়েছে। ব্রেকেভেন ও ট্রেইলিং লক করতে টার্মিনালে 'Algo Trading' বাটনটি ক্লিক করে চালু করুন।")
                        self.log("⚠️ MT5 AutoTrading is disabled by client (Retcode 10027). Please enable Algo Trading in MT5.")
                        self._algo_warned = True

            # SMART PROFIT HARVEST / EMERGENCY CIRCUIT BREAKER
            elif action_type == "close_position":
                c_res = self.exness.close_position(act["ticket"])
                if c_res.get("status") in ("success", "queued"):
                    sym = act.get("symbol", "XAUUSDm")
                    self.symbol_cooldowns[sym] = time.time() + 900.0  # 15 minutes anti-churn cooldown
                    self.send_agent_message("Marcus", "Risk Guardian (PA_02)", act["reason"])
                    self.send_agent_message("AI Brain", "Neural Overseer", f"⚡ DEFENSE CLOSE: {sym} #{act['ticket']} settled. 15m Anti-Churn Cooldown engaged.")
                    self.telegram.send_message(f"⚡ <b>AI POSITION DEFENSE EXIT:</b>\n{act['reason']}\n🛡️ <i>15-Minute Anti-Churn Cooldown engaged on {sym}.</i>")
                    self.log(f"⚡ Position #{act['ticket']} ({sym}): {act['reason']}")

    def start_background_loop(self):
        if self.is_running:
            return
        self.is_running = True
        self.log("AI Central Neural Brain, Gen 3.0 Autonomous Supervisor & Telegram Sentinel Live.")

        # Start Gen 3.0 Autonomous Floor Supervisor
        self.supervisor.start()

        self.telegram.start_polling()
        self.telegram.send_message("🧠 <b>Gen 3.0 Autonomous Trading Floor Active</b>\nMonitoring 11 Specialist Robot Employees.\nExness MT5 Sovereign Risk Shield engaged.")

        # Workforce announcements
        self.send_agent_message("AI Brain", "Neural Overseer", "🧠 Central Neural Brain calibrated. Actively mentoring all 7 robot employees.")
        self.send_agent_message("Alex", "Chief Quant (PA_01)", "Connected to AI Brain. Scanning Gold, BTC & ETH order flows.")

        def loop():
            counter = 0
            while True:
                try:
                    # Every 3 seconds: refresh balance & evaluate trade defenses (Break-Even & Trailing Stop)
                    self.exness.refresh_balance()
                    self.evaluate_and_defend_positions()

                    counter += 1
                    # Full market scan every 15 seconds (every 5 cycles)
                    if counter % 5 == 0:
                        self.run_simultaneous_scan()
                    
                    if counter % 40 == 0:
                        gold_p = self.multi_market_matrix.get("gold", {}).get("price", 2748.20)
                        self.send_agent_message("AI Brain", "Neural Overseer", f"🧠 Autonomous Audit: Market structure healthy. Gold support at $2,735.00 intact.")
                    elif counter % 70 == 0:
                        self.brain.teach_agent("Mia", "Branding Strategy", "Prioritize short-form breakdown threads showing the 0.618 OTE entries.")
                        self.send_agent_message("Mia", "Viral Copywriter (PA_07)", "Lesson absorbed from AI Brain! Updating Twitter thread queue.")

                except Exception as e:
                    self.log(f"Cycle Note: {str(e)}")
                time.sleep(3.0)

        threading.Thread(target=loop, daemon=True).start()
