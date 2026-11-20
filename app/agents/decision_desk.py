"""
Generation 3.0: Sovereign Decision Desk & Multi-Agent Consensus Hub
Features:
- Multi-Agent Deliberation (7 Specialists: Trend, Momentum, Liquidity, Session, Sentiment, Macro, and Adversarial Red Team).
- Market Regime Engine: Classifies structure (Trending, Accumulation, Chop, News Shock) and adapts target R:R.
- Red Team Prosecutor: Adversarial audit to detect liquidity traps, momentum chasing, and choke SLs.
- Sovereign Portfolio Engine: Fractional Kelly sizing + Cross-asset correlation defense.
- Autonomous Circuit Breakers: Cooldown on losing streaks, news buffers, and spread surges.
- Strategy Evolver: Vetoes quarantined setups with negative statistical expectancy.
- Full SQLite logging for machine learning and audit.
"""
from typing import Dict, Any, List, Optional
import pandas as pd

from app.agents.trend_agent import TrendAnalyst
from app.agents.momentum_agent import MomentumAnalyst
from app.agents.liquidity_agent import LiquidityAnalyst
from app.agents.session_agent import SessionVolatilityAnalyst
from app.agents.sentiment_agent import SentimentAnalyst
from app.agents.macro_agent import MacroCrossAssetAnalyst
from app.agents.red_team_agent import RedTeamProsecutor
from app.agents.regime_classifier import MarketRegimeEngine
from app.trading.risk_manager import RiskManager
from app.trading.portfolio_engine import SovereignPortfolioEngine
from app.trading.circuit_breaker import AutonomousCircuitBreaker
from app.learning.journal import TradeJournal
from app.learning.strategy_evolver import StrategyEvolver


class DecisionDesk:
    def __init__(
        self,
        risk_manager: Optional[RiskManager] = None,
        journal: Optional[TradeJournal] = None,
        confidence_threshold: float = 70.0,
        min_rrr: float = 2.0,
        circuit_breaker: Optional[AutonomousCircuitBreaker] = None,
        portfolio_engine: Optional[SovereignPortfolioEngine] = None,
        strategy_evolver: Optional[StrategyEvolver] = None
    ):
        self.risk_manager = risk_manager or RiskManager()
        self.journal = journal or TradeJournal()
        self.confidence_threshold = confidence_threshold
        self.min_rrr = min_rrr

        # Gen 3.0 Specialists & Engines
        self.trend_agent = TrendAnalyst()
        self.momentum_agent = MomentumAnalyst()
        self.liquidity_agent = LiquidityAnalyst()
        self.session_agent = SessionVolatilityAnalyst()
        self.sentiment_agent = SentimentAnalyst()
        self.macro_agent = MacroCrossAssetAnalyst()
        self.red_team = RedTeamProsecutor()
        self.regime_engine = MarketRegimeEngine()
        self.circuit_breaker = circuit_breaker or AutonomousCircuitBreaker()
        self.portfolio_engine = portfolio_engine or SovereignPortfolioEngine()
        self.strategy_evolver = strategy_evolver or StrategyEvolver(journal=self.journal)

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
        news_blackout: bool = False,
        macro_feed: Optional[Dict[str, Any]] = None,
        setup_name: str = "MULTI_AGENT_DESK"
    ) -> Dict[str, Any]:
        """
        Conducts Gen 3.0 multi-agent debate, regime classification, Red Team audit,
        circuit breaker verification, and sovereign risk sizing.
        """
        if df_m15.empty or len(df_m15) < 30:
            return {
                "approved": False,
                "reason": "Insufficient candles for multi-agent deliberation",
                "symbol": symbol
            }

        last_close = float(df_m15["close"].iloc[-1])
        spread = float(market_metrics.get("spread", 0.0))
        baseline_spread = float(market_metrics.get("avg_spread", self.max_spreads.get(symbol, 0.30)))

        # 1. Autonomous Circuit Breakers Audit
        cb_audit = self.circuit_breaker.audit_trade_permission(
            symbol=symbol,
            current_spread=spread,
            baseline_spread=baseline_spread,
            news_blackout=news_blackout
        )
        if not cb_audit.get("permitted"):
            return {
                "approved": False,
                "reason": f"🛑 CIRCUIT BREAKER VETO: {cb_audit.get('reason')}",
                "symbol": symbol,
                "circuit_breakers": cb_audit.get("active_breakers")
            }

        # 2. Strategy Evolver Quarantine Check
        if self.strategy_evolver.is_setup_quarantined(setup_name):
            rejection = f"🛑 SETUP QUARANTINED: Setup '{setup_name}' has negative statistical edge. Execution barred."
            return {"approved": False, "reason": rejection, "symbol": symbol}

        # 3. Market Regime Classification
        regime_data = self.regime_engine.classify_regime(df_m15, market_metrics)
        if regime_data.get("regime") == "NEWS_SHOCK_EVENT":
            rejection = f"🛑 REGIME VETO: {regime_data.get('notes')}"
            return {"approved": False, "reason": rejection, "symbol": symbol, "regime": regime_data}

        # 4. Spread Ceiling Filter
        max_allowed_spread = self.max_spreads.get(symbol, 0.50)
        if spread > max_allowed_spread:
            return {
                "approved": False,
                "reason": f"🛑 SPREAD REJECTION: Current spread {spread:.4f} exceeds ceiling {max_allowed_spread:.4f}",
                "symbol": symbol
            }

        # 5. Run Specialists
        trend_out = self.trend_agent.analyze(df_m15)
        momentum_out = self.momentum_agent.analyze(df_m15)
        liquidity_out = self.liquidity_agent.analyze(df_m15)
        session_out = self.session_agent.analyze(df_m15, market_metrics, news_blackout=news_blackout)
        sentiment_out = self.sentiment_agent.analyze(symbol)
        macro_out = self.macro_agent.analyze_macro_context(symbol, macro_feed=macro_feed)

        agent_opinions = {
            "trend": trend_out,
            "momentum": momentum_out,
            "liquidity": liquidity_out,
            "session": session_out,
            "sentiment": sentiment_out,
            "macro": macro_out
        }

        # 6. Consensus & Agreement Counting
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

        # 7. Dynamic Invalidation & Target Levels (Structural SL / TP with Regime Multiplier)
        target_mult = regime_data.get("target_multiplier", 1.0)
        adjusted_rrr = max(1.8, round(self.min_rrr * target_mult, 2))

        if consensus_bias == "BUY":
            inval = liquidity_out.get("invalidation_level") or trend_out.get("invalidation_level")
            sl = float(inval) if inval and inval < last_close else round(last_close - (market_metrics.get("atr_14", 1.5) * 1.5), 2)
            risk_dist = abs(last_close - sl)
            # Calibrated Gold Intraday SL ($3.00 - $4.20) and TP ($6.00 - $8.50) for realistic breathing room
            if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
                risk_dist = max(2.80, min(risk_dist, 4.20))
                sl = round(last_close - risk_dist, 2)
                tp_dist = min(max(risk_dist * adjusted_rrr, 6.00), 8.50)
                tp = round(last_close + tp_dist, 2)
            else:
                tp = round(last_close + (risk_dist * adjusted_rrr), 2)
        elif consensus_bias == "SELL":
            inval = liquidity_out.get("invalidation_level") or trend_out.get("invalidation_level")
            sl = float(inval) if inval and inval > last_close else round(last_close + (market_metrics.get("atr_14", 1.5) * 1.5), 2)
            risk_dist = abs(sl - last_close)
            # Calibrated Gold Intraday SL ($3.00 - $4.20) and TP ($6.00 - $8.50) for realistic breathing room
            if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
                risk_dist = max(2.80, min(risk_dist, 4.20))
                sl = round(last_close + risk_dist, 2)
                tp_dist = min(max(risk_dist * adjusted_rrr, 6.00), 8.50)
                tp = round(last_close - tp_dist, 2)
            else:
                tp = round(last_close - (risk_dist * adjusted_rrr), 2)
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
            "regime": regime_data.get("regime", "UNKNOWN"),
            "adjusted_rrr": adjusted_rrr
        }

        # 8. Consensus & Threshold Validation
        trigger_reason = f"Consensus {consensus_bias} ({agreement_count}/6 agents, Conf: {net_confidence}%, Regime: {regime_data.get('regime')})"
        if consensus_bias == "NEUTRAL" or agreement_count < 3:
            rejection_reason = f"Lack of consensus (Buy: {buy_votes}, Sell: {sell_votes}). Requires >= 3 agreeing agents."
            self.journal.log_decision_event(
                symbol=symbol, timeframe="M15", consensus_bias="NEUTRAL", confidence=net_confidence,
                agreement_count=agreement_count, trigger_reason=rejection_reason, entry_price=last_close,
                stop_loss=sl, take_profit=tp, agent_votes=agent_opinions, features_snapshot=features_snapshot,
                risk_status="VETOED", risk_reason=rejection_reason, executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions, "regime": regime_data}

        if net_confidence < self.confidence_threshold:
            rejection_reason = f"Confidence {net_confidence}% below threshold {self.confidence_threshold}%"
            self.journal.log_decision_event(
                symbol=symbol, timeframe="M15", consensus_bias=consensus_bias, confidence=net_confidence,
                agreement_count=agreement_count, trigger_reason=trigger_reason, entry_price=last_close,
                stop_loss=sl, take_profit=tp, agent_votes=agent_opinions, features_snapshot=features_snapshot,
                risk_status="VETOED", risk_reason=rejection_reason, executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions, "regime": regime_data}

        # 9. Adversarial Red Team Scrutiny ("The Prosecutor")
        red_team_audit = self.red_team.scrutinize_proposal(
            symbol=symbol,
            proposed_side=consensus_bias,
            entry_price=last_close,
            stop_loss=sl,
            take_profit=tp,
            df_candles=df_m15,
            market_metrics=market_metrics,
            agent_opinions=agent_opinions
        )

        agent_opinions["red_team"] = red_team_audit

        if red_team_audit.get("veto_recommended"):
            rejection_reason = f"🛑 RED TEAM PROSECUTOR VETO (Risk: {red_team_audit.get('risk_score')}/100): {'; '.join(red_team_audit.get('critique', []))}"
            self.journal.log_decision_event(
                symbol=symbol, timeframe="M15", consensus_bias=consensus_bias, confidence=net_confidence,
                agreement_count=agreement_count, trigger_reason=trigger_reason, entry_price=last_close,
                stop_loss=sl, take_profit=tp, agent_votes=agent_opinions, features_snapshot=features_snapshot,
                risk_status="VETOED", risk_reason=rejection_reason, executed=False
            )
            return {
                "approved": False,
                "reason": rejection_reason,
                "symbol": symbol,
                "agent_opinions": agent_opinions,
                "red_team_audit": red_team_audit,
                "regime": regime_data
            }

        # 10. Submit to Sovereign Risk Manager for Base Capital Limits
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
                symbol=symbol, timeframe="M15", consensus_bias=consensus_bias, confidence=net_confidence,
                agreement_count=agreement_count, trigger_reason=trigger_reason, entry_price=last_close,
                stop_loss=sl, take_profit=tp, agent_votes=agent_opinions, features_snapshot=features_snapshot,
                risk_status="VETOED", risk_reason=rejection_reason, executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions, "regime": regime_data}

        # 11. Portfolio Correlation & Fractional Kelly Fine-Tuning
        corr_check = self.portfolio_engine.check_portfolio_correlation_risk(
            symbol=symbol,
            dollar_risk=risk_plan["dollar_risk"],
            account_balance=account_equity,
            open_positions=open_positions
        )
        if not corr_check.get("approved"):
            rejection_reason = f"🛑 PORTFOLIO CORRELATION VETO: {corr_check.get('reason')}"
            self.journal.log_decision_event(
                symbol=symbol, timeframe="M15", consensus_bias=consensus_bias, confidence=net_confidence,
                agreement_count=agreement_count, trigger_reason=trigger_reason, entry_price=last_close,
                stop_loss=sl, take_profit=tp, agent_votes=agent_opinions, features_snapshot=features_snapshot,
                risk_status="VETOED", risk_reason=rejection_reason, executed=False
            )
            return {"approved": False, "reason": rejection_reason, "symbol": symbol, "agent_opinions": agent_opinions, "regime": regime_data}

        # 12. Approved Institutional Execution Plan
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
            risk_reason="Passed all 7-Agent debates, Red Team Prosecutor, and Sovereign Risk controls",
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
            "risk_reward_ratio": round(abs(tp - last_close) / max(abs(last_close - sl), 0.001), 2),
            "confidence": net_confidence,
            "agreement_count": agreement_count,
            "trigger_reason": trigger_reason,
            "agent_opinions": agent_opinions,
            "red_team_audit": red_team_audit,
            "regime": regime_data,
            "circuit_breaker": cb_audit
        }

        return decision_ticket
