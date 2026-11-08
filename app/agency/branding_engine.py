"""
In-House Automated Media & Branding Division
Autonomous AI workers creating viral brand authority, educational threads,
and video scripts exclusively for the proprietary trading institution.
"""
from datetime import datetime
from typing import Dict, Any, List

class BrandingEngine:
    def __init__(self):
        self.content_feed: List[Dict[str, Any]] = []

    def generate_firm_content(self, trend: str, btc_price: str, last_trade: Dict[str, Any] = None) -> Dict[str, Any]:
        """Creates high-impact branding content for the trading firm."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pnl_text = f"+${last_trade.get('realized_pnl', 520):,.2f}" if last_trade else "+$500.00"
        trade_id = last_trade.get('id', 'TRADE-001') if last_trade else "SMC-SETUP"

        posts = [
            {
                "author": "Mia (Viral Copywriter)",
                "platform": "Twitter / X (Thread)",
                "type": "Trade Breakdown & Authority",
                "headline": f"How our AI Trading Desk captured {pnl_text} using SMC + Fib Retracement",
                "content": (
                    f"Institutional orderflow leaves footprints. Here's how our autonomous quant desk executed today:\n\n"
                    f"1. High Time Frame Trend confirmed {trend} on 4H candles\n"
                    f"2. Price pulled back to 50% Equilibrium into the 0.618-0.786 Golden Pocket\n"
                    f"3. Order Block & FVG mitigation confirmed\n"
                    f"4. Marcus (Risk Officer) sized position with strict 1% risk\n\n"
                    f"Result: {trade_id} delivered clean 1:2.8 RRR profit. "
                    f"Zero emotion. Pure quantitative execution. 🏛️📈\n#Trading #QuantDesk #SMC #Bitcoin"
                ),
                "created_at": now_str
            },
            {
                "author": "Noah (Reels & Script Specialist)",
                "platform": "Shorts / TikTok / Reels",
                "type": "30-Second Video Script",
                "headline": "Why 95% of Retail Traders Fail at Fibonacci",
                "content": (
                    f"[HOOK - 0:00 - 0:03]\n"
                    f"Stop drawing Fibonacci from every single random wick! Here's how institutions actually use it.\n\n"
                    f"[BODY - 0:03 - 0:20]\n"
                    f"Step 1: Check your 4H trend first. If it's {trend}, only trade in that direction.\n"
                    f"Step 2: Never buy above the 50% Equilibrium. That's retail premium.\n"
                    f"Step 3: Wait for price to touch the Golden Pocket (0.618 - 0.786). That's wholesale.\n\n"
                    f"[CALL TO ACTION - 0:20 - 0:30]\n"
                    f"Discipline beats prediction. Follow our AI trading floor for daily algorithmic breakdowns."
                ),
                "created_at": now_str
            }
        ]

        self.content_feed.extend(posts)
        if len(self.content_feed) > 25:
            self.content_feed = self.content_feed[-25:]

        return posts[0]

    def get_feed(self) -> List[Dict[str, Any]]:
        return self.content_feed
