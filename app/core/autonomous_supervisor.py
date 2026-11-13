"""
Generation 3.0: Continuous Autonomous Trading Floor Supervisor
The central autonomous governor running the 24/7 institutional trading lifecycle:
- Autonomous Tick & Candle Monitor
- Real-Time Multi-Agent Debate & Red Team Auditing
- Circuit Breaker & Peak-Equity Drawdown Monitoring
- Order Dispatch & MT5 Bridge Synchronization
- Active Trade Defense (Patient Break-Even & Wide Trailing)
- Post-Trade Forensic Dissection & Journal Evolution
"""
import time
import threading
from typing import Dict, Any, List, Optional
import pandas as pd

from app.agents.decision_desk import DecisionDesk
from app.trading.circuit_breaker import AutonomousCircuitBreaker
from app.trading.portfolio_engine import SovereignPortfolioEngine
from app.learning.strategy_evolver import StrategyEvolver
from app.learning.journal import TradeJournal
from app.data.data_collector import DataCollector
from app.data.db_manager import DatabaseManager


class AutonomousFloorSupervisor:
    def __init__(
        self,
        orchestrator=None,
        decision_desk: Optional[DecisionDesk] = None,
        circuit_breaker: Optional[AutonomousCircuitBreaker] = None,
        strategy_evolver: Optional[StrategyEvolver] = None,
        poll_interval: float = 3.0
    ):
        self.orchestrator = orchestrator
        self.db = orchestrator.db_manager if orchestrator else DatabaseManager()
        self.journal = orchestrator.journal if orchestrator else TradeJournal(db=self.db)
        self.collector = orchestrator.data_collector if orchestrator else DataCollector(db=self.db)
        self.circuit_breaker = circuit_breaker or AutonomousCircuitBreaker()
        self.portfolio_engine = SovereignPortfolioEngine()
        self.strategy_evolver = strategy_evolver or StrategyEvolver(journal=self.journal)

        self.decision_desk = decision_desk or DecisionDesk(
            risk_manager=orchestrator.risk if orchestrator else None,
            journal=self.journal,
            circuit_breaker=self.circuit_breaker,
            portfolio_engine=self.portfolio_engine,
            strategy_evolver=self.strategy_evolver
        )

        self.poll_interval = poll_interval
        self.is_running = False
        self.is_paused = False
        self._thread: Optional[threading.Thread] = None

        self.symbols = ["XAUUSDm", "BTCUSDm", "EURUSDm", "GBPUSDm"]
        self.peak_equity = 0.0
        self.last_cycle_time = 0.0
        self.cycle_count = 0
        self.active_signals: List[Dict[str, Any]] = []
        self.supervisor_events: List[Dict[str, Any]] = []

    def start(self):
        """Starts the autonomous floor supervisor background loop."""
        if self.is_running:
            return
        self.is_running = True
        self.is_paused = False
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._log_event("SUPERVISOR_STARTED", "Autonomous Floor Supervisor engaged in continuous monitoring.")

    def pause(self):
        """Pauses autonomous execution without stopping tracking."""
        self.is_paused = True
        self._log_event("SUPERVISOR_PAUSED", "Supervisor execution temporarily paused by operator.")

    def resume(self):
        """Resumes active autonomous execution."""
        self.is_paused = False
        self._log_event("SUPERVISOR_RESUMED", "Supervisor execution resumed.")

    def stop(self):
        """Stops the supervisor loop cleanly."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._log_event("SUPERVISOR_STOPPED", "Supervisor shutdown completed.")

    def _log_event(self, event_type: str, message: str):
        entry = {
            "time": time.strftime("%H:%M:%S"),
            "timestamp": time.time(),
            "type": event_type,
            "message": message
        }
        self.supervisor_events.insert(0, entry)
        if len(self.supervisor_events) > 100:
            self.supervisor_events.pop()

    def _run_loop(self):
        while self.is_running:
            try:
                if not self.is_paused:
                    self.run_supervisor_cycle()
            except Exception as e:
                self._log_event("SUPERVISOR_ERROR", f"Error in supervisor cycle: {str(e)}")
            time.sleep(self.poll_interval)

    def run_supervisor_cycle(self) -> Dict[str, Any]:
        """
        Executes one full iteration of the autonomous trading lifecycle.
        """
        self.cycle_count += 1
        self.last_cycle_time = time.time()

        balance = 50.0
        equity = 50.0
        open_positions = []
        if self.orchestrator and hasattr(self.orchestrator, "exness"):
            balance = float(getattr(self.orchestrator.exness, "balance", 50.0))
            equity = float(getattr(self.orchestrator.exness, "equity", balance))
            open_positions = getattr(self.orchestrator.exness, "open_positions", [])

        # 1. Update Peak Equity & Audit Drawdown Circuit Breaker
        if equity > self.peak_equity:
            self.peak_equity = equity

        dd_audit = self.circuit_breaker.evaluate_drawdown_state(equity, self.peak_equity)
        if dd_audit.get("kill_switch"):
            self._log_event("KILL_SWITCH_HALT", dd_audit.get("reason", "Kill switch engaged"))
            if self.orchestrator:
                self.orchestrator.log(f"🚨 {dd_audit.get('reason')}")
            return {"status": "HALTED", "reason": dd_audit.get("reason")}

        # 2. Defend Existing Positions (Patient BE + Wide Trailing)
        if self.orchestrator and hasattr(self.orchestrator, "evaluate_and_defend_positions"):
            self.orchestrator.evaluate_and_defend_positions()

        # 3. Scan Watched Symbols for Institutional Signals
        cycle_signals = []
        for sym in self.symbols:
            # Check symbol cooldown
            if self.orchestrator and hasattr(self.orchestrator, "symbol_cooldowns"):
                cd = self.orchestrator.symbol_cooldowns.get(sym, 0.0)
                if time.time() < cd:
                    continue

            # Fetch candles & metrics
            df_m15 = self._get_symbol_candles(sym)
            if df_m15.empty or len(df_m15) < 30:
                continue

            market_metrics = self._get_market_metrics(sym, df_m15)

            # Evaluate Symbol via Gen 3.0 Decision Desk
            decision = self.decision_desk.evaluate_symbol(
                symbol=sym,
                df_m15=df_m15,
                market_metrics=market_metrics,
                account_equity=equity,
                open_positions=open_positions,
                setup_name=f"GEN3_{sym}"
            )

            if decision.get("approved"):
                cycle_signals.append(decision)
                self._dispatch_order(decision)

        self.active_signals = cycle_signals
        return {
            "cycle": self.cycle_count,
            "equity": equity,
            "peak_equity": self.peak_equity,
            "drawdown_pct": dd_audit.get("drawdown_pct", 0.0),
            "stepdown_active": dd_audit.get("stepdown", False),
            "approved_signals_count": len(cycle_signals),
            "circuit_breaker": self.circuit_breaker.get_status()
        }

    def _get_symbol_candles(self, symbol: str) -> pd.DataFrame:
        """Fetches candles from orchestrator market stream or synthetic historical fallback."""
        if self.orchestrator and hasattr(self.orchestrator, "market"):
            # Check market stream candles
            market_matrix = getattr(self.orchestrator, "multi_market_matrix", {})
            sym_key = "gold" if "XAU" in symbol else ("btc" if "BTC" in symbol else "forex")
            candles = market_matrix.get(sym_key, {}).get("candles_15m")
            if candles and len(candles) >= 30:
                return pd.DataFrame(candles)

        # Fallback to database
        df_candles = self.db.get_candles_df(symbol, "M15", limit=60)
        if not df_candles.empty and len(df_candles) >= 30:
            return df_candles

        return pd.DataFrame()

    def _get_market_metrics(self, symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates live volatility and spread metrics."""
        closes = df["close"].astype(float)
        highs = df["high"].astype(float)
        lows = df["low"].astype(float)

        # ATR calculation
        tr = pd.concat([
            highs - lows,
            abs(highs - closes.shift(1)),
            abs(lows - closes.shift(1))
        ], axis=1).max(axis=1)
        atr_14 = float(tr.rolling(14).mean().iloc[-1]) if len(tr) >= 14 else 1.5

        # Spread lookup
        spread = 0.25 if "XAU" in symbol else (15.0 if "BTC" in symbol else 0.00018)
        if self.orchestrator and hasattr(self.orchestrator, "exness"):
            for p in getattr(self.orchestrator.exness, "open_positions", []):
                if p.get("symbol") == symbol and "spread" in p:
                    spread = float(p["spread"])

        return {
            "spread": spread,
            "avg_spread": spread,
            "atr_14": round(atr_14, 2),
            "rsi_14": 52.0,
            "session": "LONDON_NY_OVERLAP"
        }

    def _dispatch_order(self, decision: Dict[str, Any]):
        """Dispatches an approved multi-agent trade to MT5 and records telemetry."""
        sym = decision["symbol"]
        side = decision["side"]
        vol = decision["volume"]
        sl = decision["stop_loss"]
        tp = decision["take_profit"]

        self._log_event(
            "ORDER_DISPATCH",
            f"🚀 EXECUTING {side} {vol} {sym} @ market. SL: ${sl:.2f} | TP: ${tp:.2f} | Conf: {decision['confidence']}%"
        )

        if self.orchestrator and hasattr(self.orchestrator, "exness"):
            res = self.orchestrator.exness.execute_live_order(sym, side, volume=vol, sl=sl, tp=tp)
            ticket = res.get("ticket", 0)

            # Record internal trade order
            if hasattr(self.orchestrator, "account"):
                order = self.orchestrator.account.open_trade({
                    "symbol": sym,
                    "side": side,
                    "volume": vol,
                    "entry_price": decision["entry_price"],
                    "sl": sl,
                    "tp": tp,
                    "dollar_risk": decision["dollar_risk"]
                }, symbol=sym)
                order["mt5_ticket"] = ticket

            # Telegram signal broadcast
            if hasattr(self.orchestrator, "telegram"):
                prosecutor_status = decision.get("red_team_audit", {}).get("prosecutor_status", "CLEAN")
                regime_name = decision.get("regime", {}).get("regime", "EXPANSION")
                signal_text = (
                    f"🏛️ <b>GEN 3.0 AUTONOMOUS SIGNAL ({sym}):</b>\n"
                    f"Action: <b>{side}</b> {vol} Lot\n"
                    f"Entry: ${decision['entry_price']:.2f}\n"
                    f"Stop Loss: ${sl:.2f} | Target: ${tp:.2f} (R:R {decision['risk_reward_ratio']}R)\n"
                    f"Consensus: {decision['agreement_count']}/6 Specialists ({decision['confidence']}%)\n"
                    f"Regime: <code>{regime_name}</code> | Red Team: <code>{prosecutor_status}</code>"
                )
                self.orchestrator.telegram.send_notification(signal_text)

    def get_telemetry(self) -> Dict[str, Any]:
        """Provides full institutional telemetry snapshot for the Web UI."""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "cycle_count": self.cycle_count,
            "last_cycle_time": self.last_cycle_time,
            "peak_equity": round(self.peak_equity, 2),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "quarantined_setups": self.strategy_evolver.quarantined_setups,
            "recent_events": self.supervisor_events[:15],
            "active_signals": self.active_signals
        }
