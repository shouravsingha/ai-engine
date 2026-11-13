"""
Adversarial Red Team Agent ("The Institutional Prosecutor")
Sole mission: Act as devil's advocate, rigorously scrutinize trade proposals,
and identify dangerous traps, choked stops, and adverse structural factors
to prevent low-edge executions.
"""
from typing import Dict, Any, List
import pandas as pd


class RedTeamProsecutor:
    def __init__(self, max_allowed_risk_score: float = 65.0):
        self.max_allowed_risk_score = max_allowed_risk_score

    def scrutinize_proposal(
        self,
        symbol: str,
        proposed_side: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        df_candles: pd.DataFrame,
        market_metrics: Dict[str, Any],
        agent_opinions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conducts adversarial interrogation of the trade setup.
        Returns veto recommendation, calculated risk score (0-100), and specific critique points.
        """
        critique_points: List[str] = []
        risk_score = 0.0

        if df_candles.empty or len(df_candles) < 20:
            return {
                "veto_recommended": True,
                "risk_score": 100.0,
                "critique": ["Insufficient market data for risk audit"],
                "passed": False
            }

        last_close = float(df_candles["close"].iloc[-1])
        spread = float(market_metrics.get("spread", 0.0))
        atr = float(market_metrics.get("atr_14", 1.5))
        risk_dist = abs(entry_price - stop_loss)

        # 1. Critical Choke Stop Check: Stop loss distance is tighter than spread or < 0.35x ATR
        if risk_dist < (spread * 2.2):
            risk_score += 45.0
            critique_points.append(f"Choke Warning: Stop loss distance ({risk_dist:.2f}) is too tight for spread ({spread:.2f}). High probability of noise stop-out.")

        if atr > 0 and risk_dist < (atr * 0.35):
            risk_score += 25.0
            critique_points.append(f"Sub-ATR Vulnerability: SL distance is under 35% of 14-period ATR ({atr:.2f}). Normal candle vibration will hit stop.")

        # 2. Check Over-Extended Momentum (Chasing Price after 4+ consecutive candles)
        recent_closes = df_candles["close"].iloc[-5:].tolist()
        if proposed_side == "BUY":
            consecutive_up = sum(1 for i in range(len(recent_closes)-1) if recent_closes[i+1] > recent_closes[i])
            if consecutive_up >= 4:
                risk_score += 15.0
                critique_points.append("Momentum Over-Extension: Buying after 4+ consecutive bullish candles. Elevated pullback probability.")
        elif proposed_side == "SELL":
            consecutive_down = sum(1 for i in range(len(recent_closes)-1) if recent_closes[i+1] < recent_closes[i])
            if consecutive_down >= 4:
                risk_score += 15.0
                critique_points.append("Momentum Over-Extension: Selling after 4+ consecutive bearish candles. Elevated short-covering probability.")

        # 3. Check Extreme Liquidity Sweep Traps (Buying in the top 3% of 20-period range)
        high_20 = float(df_candles["high"].iloc[-20:].max())
        low_20 = float(df_candles["low"].iloc[-20:].min())
        range_span = max(high_20 - low_20, 0.001)

        pct_in_range = (entry_price - low_20) / range_span
        if proposed_side == "BUY" and pct_in_range > 0.98:
            risk_score += 20.0
            critique_points.append(f"Liquidity Trap: Buying in the extreme top 2% of 20-period range (${high_20:.2f}). Potential Buy-Side Liquidity (BSL) purge into supply.")
        elif proposed_side == "SELL" and pct_in_range < 0.02:
            risk_score += 20.0
            critique_points.append(f"Liquidity Trap: Selling in the extreme bottom 2% of 20-period range (${low_20:.2f}). Potential Sell-Side Liquidity (SSL) purge into demand.")

        # 4. Critical Dissent: If >= 3 agents oppose proposal
        opposing_agents = []
        for name, op in agent_opinions.items():
            if op.get("bias") and op.get("bias") != "NEUTRAL" and op.get("bias") != proposed_side:
                opposing_agents.append(f"{name} ({op.get('bias')})")

        if len(opposing_agents) >= 3:
            risk_score += 35.0
            critique_points.append(f"Majority Specialist Dissent: 3+ agents oppose proposal: {', '.join(opposing_agents)}.")

        # 5. Check Low RRR
        if risk_dist > 0:
            reward_dist = abs(take_profit - entry_price)
            rrr = reward_dist / risk_dist
            if rrr < 1.7:
                risk_score += 35.0
                critique_points.append(f"Sub-Optimal Payoff: Risk-Reward ratio {rrr:.2f} is under institutional minimum 1.70.")

        # Final verdict
        veto_recommended = risk_score > self.max_allowed_risk_score
        if not critique_points:
            critique_points.append("Prosecutor Audit Clean: Setup displays sound structural invalidation, adequate breathing room, and controlled liquidity risk.")

        return {
            "veto_recommended": veto_recommended,
            "passed": not veto_recommended,
            "risk_score": round(min(risk_score, 100.0), 1),
            "critique": critique_points,
            "prosecutor_status": "VETO_RECOMMENDED" if veto_recommended else "CLEAN_PASS"
        }
