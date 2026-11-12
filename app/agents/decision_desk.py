"""
Decision Desk & Lead Reasoner Engine for Human-Like Trading Desk.
Orchestrates debate among 5 specialist agents, enforces consensus rules:
- Requires >= 3 agents in agreement
- Confidence >= 70%
- Structural Stop Loss & Take Profit with R:R >= 1:2
- Filters high-impact news blackout & wide spreads
- Submits plan to Sovereign Risk Manager for absolute veto
- Logs every debate and feature snapshot into TradeJournal.
"""

from typing import Dict, Any, List, Optional
import pandas as pd

from app.agents.trend_agent import TrendAnalyst
from app.agents.momentum_agent import MomentumAnalyst
from app.agents.liquidity_agent import LiquidityAnalyst
from app.agents.session_agent import SessionVolatilityAnalyst
from app.agents.sentiment_agent import SentimentAnalyst
from app.trading.risk_manager import RiskManager
from app.learning.journal import TradeJournal


class DecisionDesk:
    def __init__(
        self,
        risk_manager: Optional[RiskManager] = None,
        journal: Optional[TradeJournal] = None,
        confidence_threshold: float = 70.0,
        min_rrr: float = 2.0
    ):
        self.risk_manager = risk_manager or RiskManager()
        self.journal = journal or TradeJournal()
        self.confidence_threshold = confidence_threshold
        self.min_rrr = min_rrr

        # Specialist Agents
        self.trend_agent = TrendAnalyst()
        self.momentum_agent = MomentumAnalyst()
        self.liquidity_agent = LiquidityAnalyst()
        self.session_agent = SessionVolatilityAnalyst()
        self.sentiment_agent = SentimentAnalyst()

        # Spread ceilings per symbol to prevent excessive friction
        self.max_spreads = {
            "XAUUSDm": 0.45,
            "BTCUSDm": 25.0,
            "EURUSDm": 0.00025,
            "GBPUSDm": 0.00030
        }

    def evaluate_symbol(
        self,
        symbol: str,
        df_m15: pd.DataFrame,
        market_metrics: Dict[str, Any],
        account_equity: float,
        open_positions: Optional[List[Dict[str, Any]]] = None,
        news_blackout: bool = False
    ) -> Dict[str, Any]:
        """
        Conducts full multi-agent debate and produces an institutional trade decision.
        """
        if df_m15.empty or len(df_m15) < 30:
            return {
                "approved": False,
                "reason": "Insufficient candles for multi-agent deliberation",
                "symbol": symbol
            }

        last_close = float(df_m15["close"].iloc[-1])
        spread = float(market_metrics.get("spread", 0.0))

        # 1. Spread Filter
        max_allowed_spread = self.max_spreads.get(symbol, 0.50)
        if spread > max_allowed_spread:
            return {
                "approved": False,
                "reason": f"🛑 SPREAD REJECTION: Current spread {spread:.4f} exceeds ceiling {max_allowed_spread:.4f}",
                "symbol": symbol
            }

        # 2. Run All 5 Specialist Agents
        trend_out = self.trend_agent.analyze(df_m15)
        momentum_out = self.momentum_agent.analyze(df_m15)
        liquidity_out = self.liquidity_agent.analyze(df_m15)
        session_out = self.session_agent.analyze(df_m15, market_metrics, news_blackout=news_blackout)
        sentiment_out = self.sentiment_agent.analyze(symbol)

        agent_opinions = {
            "trend": trend_out,
            "momentum": momentum_out,
            "liquidity": liquidity_out,
            "session": session_out,
            "sentiment": sentiment_out
        }

        # 3. Consensus & Agreement Counting
        buy_votes = 0
        sell_votes = 0
        buy_weight = 0.0
        sell_weight = 0.0
        buy_weight_sum = 0.0
        sell_weight_sum = 0.0

        for key, opinion in agent_opinions.items():
            bias = opinion.get("bias", "NEUTRAL")
            conf = float(opinion.get("confidence", 0.0))
            weight = float(opinion.get("weight", 1.0))

            if bias == "BUY":
                buy_votes += 1
                buy_weight += (conf * weight)
                buy_weight_sum += weight
            elif bias == "SELL":
                sell_votes += 1
                sell_weight += (conf * weight)
                sell_weight_sum += weight

        consensus_bias = "NEUTRAL"
        agreement_count = 0
        net_confidence = 0.0

        if buy_votes >= 3 and buy_votes > sell_votes:
            consensus_bias = "BUY"
            agreement_count = buy_votes
            net_confidence = round(buy_weight / max(buy_weight_sum, 0.001), 1)
        elif sell_votes >= 3 and sell_votes > buy_votes:
            consensus_bias = "SELL"
            agreement_count = sell_votes
            net_confidence = round(sell_weight / max(sell_weight_sum, 0.001), 1)

        # 4. Invalidation & Target Levels (Structural SL / TP)
        # Use structural invalidation from liquidity or trend specialist
        if consensus_bias == "BUY":
            inval = liquidity_out.get("invalidation_level") or trend_out.get("invalidation_level")
            sl = float(inval) if inval and inval < last_close else round(last_close - (market_metrics.get("atr_14", 1.5) * 1.5), 2)
            risk_dist = abs(last_close - sl)
            tp = round(last_close + (risk_dist * self.min_rrr), 2)
        elif consensus_bias == "SELL":
            inval = liquidity_out.get("invalidation_level") or trend_out.get("invalidation_level")
            sl = float(inval) if inval and inval > last_close else round(last_close + (market_metrics.get("atr_14", 1.5) * 1.5), 2)
            risk_dist = abs(sl - last_close)
            tp = round(last_close - (risk_dist * self.min_rrr), 2)
        else:
            sl = 0.0
            tp = 0.0

        # Features Snapshot for Machine Learning & Audit
        features_snapshot = {
            "last_close": last_close,
            "spread": spread,
            "atr_14": market_metrics.get("atr_14", 0.0),
            "rsi_14": market_metrics.get("rsi_14", 50.0),
            "session": market_metrics.get("session", "UNKNOWN"),
            "ema_20": market_metrics.get("ema_20", 0.0),
            "ema_50": market_metrics.get("ema_50", 0.0)
        }

        # 5. Threshold Checks
        trigger_reason = f"Consensus {consensus_bias} ({agreement_count}/5 agents, Conf: {net_confidence}%)"
        if consensus_bias == "NEUTRAL" or agreement_count < 3:
            rejection_reason = f"Lack of consensus (Buy: {buy_votes}, Sell: {sell_votes}). Requires >= 3 agreeing agents."
            self.journal.log_decision_event(
                symbol=symbol,
                timeframe="M15",
                consensus_bias="NEUTRAL",
                confidence=net_confidence,
                agreement_count=agreement_count,
                trigger_reason=rejection_reason,
                entry_price=last_close,
                stop_loss=sl,
                take_profit=tp,
                agent_votes=agent_opinions,
                features_snapshot=features_snapshot,
                risk_status="VETOED",
                risk_reason=rejection_reason,
                executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions}

        if net_confidence < self.confidence_threshold:
            rejection_reason = f"Confidence {net_confidence}% below institutional threshold {self.confidence_threshold}%"
            self.journal.log_decision_event(
                symbol=symbol,
                timeframe="M15",
                consensus_bias=consensus_bias,
                confidence=net_confidence,
                agreement_count=agreement_count,
                trigger_reason=trigger_reason,
                entry_price=last_close,
                stop_loss=sl,
                take_profit=tp,
                agent_votes=agent_opinions,
                features_snapshot=features_snapshot,
                risk_status="VETOED",
                risk_reason=rejection_reason,
                executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions}

        # 6. Submit to Sovereign Risk Manager for Absolute Veto
        risk_plan = self.risk_manager.evaluate_and_size_trade(
            account_balance=account_equity,
            side=consensus_bias,
            entry_price=last_close,
            stop_loss=sl,
            take_profit=tp,
            symbol=symbol,
            open_positions=open_positions
        )

        if not risk_plan or not risk_plan.get("approved"):
            rejection_reason = "Sovereign Risk Manager Veto: Exceeded capital risk, missing SL, or violated daily/kill-switch limit."
            self.journal.log_decision_event(
                symbol=symbol,
                timeframe="M15",
                consensus_bias=consensus_bias,
                confidence=net_confidence,
                agreement_count=agreement_count,
                trigger_reason=trigger_reason,
                entry_price=last_close,
                stop_loss=sl,
                take_profit=tp,
                agent_votes=agent_opinions,
                features_snapshot=features_snapshot,
                risk_status="VETOED",
                risk_reason=rejection_reason,
                executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions}

        # 7. Decision Approved
        decision_id = self.journal.log_decision_event(
            symbol=symbol,
            timeframe="M15",
            consensus_bias=consensus_bias,
            confidence=net_confidence,
            agreement_count=agreement_count,
            trigger_reason=trigger_reason,
            entry_price=last_close,
            stop_loss=sl,
            take_profit=tp,
            agent_votes=agent_opinions,
            features_snapshot=features_snapshot,
            risk_status="APPROVED",
            risk_reason="Passed all multi-agent consensus and sovereign risk checks",
            executed=True
        )

        decision_ticket = {
            "approved": True,
            "decision_id": decision_id,
            "symbol": symbol,
            "side": consensus_bias,
            "entry_price": last_close,
            "stop_loss": sl,
            "take_profit": tp,
            "volume": risk_plan["volume"],
            "dollar_risk": risk_plan["dollar_risk"],
            "risk_reward_ratio": risk_plan["risk_reward_ratio"],
            "confidence": net_confidence,
            "agreement_count": agreement_count,
            "trigger_reason": trigger_reason,
            "agent_opinions": agent_opinions
        }

        return decision_ticket
