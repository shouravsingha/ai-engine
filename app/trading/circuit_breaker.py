"""
Institutional Autonomous Circuit Breakers & Streak Protection
Enforces non-negotiable defensive circuit breakers:
1. Consecutive Loss Cooldown: 3 consecutive losses = 90-minute trading timeout.
2. Drawdown Step-Down: Drawdown > 2.0% cuts max risk per trade by 50%.
3. Spread Explosion Guard: Spread > 2.0x baseline triggers instant entry veto.
4. High-Impact News Buffer: 15-minute freeze around Tier-1 news releases.
5. Catastrophic Kill-Switch: 10% total drawdown halts all execution.
"""
import time
from typing import Dict, Any, List, Optional


class AutonomousCircuitBreaker:
    def __init__(
        self,
        max_consecutive_losses: int = 3,
        streak_cooldown_seconds: float = 5400.0,  # 90 minutes
        stepdown_drawdown_pct: float = 2.0,      # 2% drawdown cuts risk
        kill_switch_dd_pct: float = 10.0         # 10% emergency halt
    ):
        self.max_consecutive_losses = max_consecutive_losses
        self.streak_cooldown_seconds = streak_cooldown_seconds
        self.stepdown_drawdown_pct = stepdown_drawdown_pct
        self.kill_switch_dd_pct = kill_switch_dd_pct

        self.consecutive_losses = 0
        self.cooldown_until: float = 0.0
        self.stepdown_active = False
        self.kill_switch_active = False
        self.circuit_events: List[Dict[str, Any]] = []

    def record_trade_outcome(self, pnl: float):
        """Records trade result to track streaks and trigger cooldowns."""
        now = time.time()
        if pnl < -0.01:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.max_consecutive_losses:
                self.cooldown_until = now + self.streak_cooldown_seconds
                event = {
                    "time": now,
                    "type": "STREAK_COOLDOWN",
                    "reason": f"🛑 CONSECUTIVE LOSS COOLDOWN: {self.consecutive_losses} losses in a row. 90-minute trading freeze engaged."
                }
                self.circuit_events.insert(0, event)
        else:
            # Profit or break-even resets the losing streak
            self.consecutive_losses = 0

    def evaluate_drawdown_state(self, current_equity: float, peak_equity: float) -> Dict[str, Any]:
        """Audits drawdown thresholds for risk stepdown or emergency halt."""
        if peak_equity <= 0:
            return {"permitted": True, "stepdown": False, "kill_switch": False}

        drawdown_pct = max(0.0, ((peak_equity - current_equity) / peak_equity) * 100.0)

        # 1. Catastrophic Kill Switch
        if drawdown_pct >= self.kill_switch_dd_pct:
            self.kill_switch_active = True
            return {
                "permitted": False,
                "stepdown": True,
                "kill_switch": True,
                "drawdown_pct": round(drawdown_pct, 2),
                "reason": f"🚨 EMERGENCY KILL SWITCH ENGAGED: Drawdown {drawdown_pct:.1f}% reached {self.kill_switch_dd_pct}% ceiling. All trading halted."
            }

        # 2. Risk Step-Down (Halving risk on 2%+ drawdown)
        if drawdown_pct >= self.stepdown_drawdown_pct:
            self.stepdown_active = True
            return {
                "permitted": True,
                "stepdown": True,
                "kill_switch": False,
                "drawdown_pct": round(drawdown_pct, 2),
                "risk_multiplier": 0.50,
                "reason": f"⚠️ STEP-DOWN ACTIVE: Drawdown {drawdown_pct:.1f}% > {self.stepdown_drawdown_pct}%. Position sizing halved for capital preservation."
            }

        self.stepdown_active = False
        return {
            "permitted": True,
            "stepdown": False,
            "kill_switch": False,
            "drawdown_pct": round(drawdown_pct, 2),
            "risk_multiplier": 1.00
        }

    def audit_trade_permission(
        self,
        symbol: str,
        current_spread: float,
        baseline_spread: float,
        news_blackout: bool = False
    ) -> Dict[str, Any]:
        """
        Audits all circuit breakers for trade authorization.
        """
        now = time.time()
        active_breakers = []

        if self.kill_switch_active:
            return {
                "permitted": False,
                "active_breakers": ["KILL_SWITCH_ACTIVE"],
                "reason": "Emergency Kill Switch is actively halting all trading activity."
            }

        # Check Streak Cooldown
        if now < self.cooldown_until:
            rem_minutes = int((self.cooldown_until - now) // 60) + 1
            active_breakers.append(f"STREAK_COOLDOWN_{rem_minutes}m")
            return {
                "permitted": False,
                "active_breakers": active_breakers,
                "reason": f"Consecutive loss streak cooldown active. {rem_minutes} minute(s) remaining."
            }

        # Check News Blackout
        if news_blackout:
            active_breakers.append("NEWS_BLACKOUT_WINDOW")
            return {
                "permitted": False,
                "active_breakers": active_breakers,
                "reason": "High-impact economic news event window active. Market orders frozen."
            }

        # Check Spread Surge
        if baseline_spread > 0 and (current_spread / baseline_spread) >= 2.0 and current_spread > 0.40:
            active_breakers.append("SPREAD_EXPLOSION")
            return {
                "permitted": False,
                "active_breakers": active_breakers,
                "reason": f"Abnormal spread spike: Current spread {current_spread:.2f} is 2x baseline {baseline_spread:.2f}."
            }

        return {
            "permitted": True,
            "active_breakers": ["STEP_DOWN_ACTIVE"] if self.stepdown_active else [],
            "stepdown": self.stepdown_active,
            "reason": "All circuit breakers clear."
        }

    def reset_kill_switch(self):
        """Manually or autonomously resets the emergency kill switch."""
        self.kill_switch_active = False
        self.stepdown_active = False
        self.consecutive_losses = 0

    def get_status(self) -> Dict[str, Any]:
        now = time.time()
        cooldown_rem = max(0, int(self.cooldown_until - now))
        return {
            "kill_switch_active": self.kill_switch_active,
            "consecutive_losses": self.consecutive_losses,
            "cooldown_remaining_seconds": cooldown_rem,
            "is_cooling_down": cooldown_rem > 0,
            "stepdown_active": self.stepdown_active,
            "events_count": len(self.circuit_events)
        }
