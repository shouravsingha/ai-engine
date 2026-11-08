import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.orchestrator import MasterOrchestrator

app = FastAPI(title="SMC & Fibonacci Quant Desk + AI Social Media Agency Engine")
orchestrator = MasterOrchestrator()

@app.on_event("startup")
def startup_event():
    orchestrator.start_background_loop()

@app.get("/api/telemetry")
def get_telemetry():
    return JSONResponse({
        "account": orchestrator.account.get_summary(),
        "open_trades": orchestrator.account.open_trades,
        "trade_history": orchestrator.account.trade_history[-10:],
        "market_analysis": orchestrator.last_analysis,
        "social_posts": orchestrator.social.get_recent_posts(),
        "leads": orchestrator.leads.get_leads(),
        "logs": orchestrator.system_logs
    })

class LeadInput(BaseModel):
    name: str
    email: str
    company: Optional[str] = "Independent"
    budget: Optional[str] = "$2,500 - $5,000"
    service: Optional[str] = "Full AI Workflow & Social Media Automation"

@app.post("/api/lead")
def submit_lead(lead: LeadInput):
    record = orchestrator.leads.process_lead(
        name=lead.name,
        email=lead.email,
        company=lead.company,
        budget=lead.budget,
        service=lead.service
    )
    orchestrator.log(f"🎯 INBOUND LEAD: {record['name']} ({record['company']}) - Tier: {record['tier']}")
    return {"status": "success", "lead": record}

@app.get("/", response_class=HTMLResponse)
def control_center():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Institutional SMC Quant Desk & AI Agency</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #07090e;
                --card: #0f141f;
                --border: #1a2333;
                --accent-blue: #38bdf8;
                --accent-green: #10b981;
                --accent-red: #f43f5e;
                --accent-gold: #f59e0b;
                --text: #f1f5f9;
                --muted: #8292a8;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                padding: 24px;
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            .container { max-width: 1350px; margin: auto; }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, #0e1726, #111a2e);
                padding: 24px 28px;
                border-radius: 16px;
                border: 1px solid var(--border);
                margin-bottom: 24px;
            }
            .title-area h1 { margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
            .title-area p { margin: 6px 0 0 0; color: var(--muted); font-size: 14px; }
            .badge-live {
                background: rgba(16, 185, 129, 0.15);
                color: var(--accent-green);
                border: 1px solid #059669;
                padding: 8px 16px;
                border-radius: 30px;
                font-size: 13px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .pulse {
                width: 10px; height: 10px; background: var(--accent-green); border-radius: 50%;
                box-shadow: 0 0 12px var(--accent-green); animation: pulse 1.8s infinite;
            }
            @keyframes pulse { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }
            
            .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px; margin-bottom: 24px; }
            .grid-2 { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; margin-bottom: 24px; }
            
            .card {
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 20px 22px;
            }
            .card-label { font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; }
            .card-value { font-size: 26px; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
            .card-sub { font-size: 13px; color: var(--muted); margin-top: 6px; }

            .tag { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
            .tag-green { background: rgba(16, 185, 129, 0.2); color: #34d399; }
            .tag-red { background: rgba(244, 63, 94, 0.2); color: #fb7185; }
            .tag-gold { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }

            table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
            th { text-align: left; padding: 12px 14px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); }
            td { padding: 12px 14px; border-bottom: 1px solid #141b29; font-family: 'JetBrains Mono', monospace; }

            .terminal {
                background: #04060a;
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 16px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                height: 240px;
                overflow-y: auto;
                color: #38bdf8;
                line-height: 1.6;
            }
            .social-card {
                background: #0b101a;
                border: 1px solid #192233;
                border-radius: 10px;
                padding: 14px;
                margin-bottom: 12px;
                font-size: 13px;
                line-height: 1.5;
            }
            @media (max-width: 900px) { .grid-2 { grid-template-columns: 1fr; } }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="title-area">
                    <h1>SMC & Fibonacci Quant Desk + AI Agency</h1>
                    <p>High Timeframe (HTF) Swing & Day Trading Architecture · Multi-Agent Workforce · Institutional Demo Desk</p>
                </div>
                <div class="badge-live">
                    <div class="pulse"></div>
                    INSTITUTIONAL CORE LIVE 24/7
                </div>
            </div>

            <!-- Top Row: Account & Capital Metrics -->
            <div class="grid-4">
                <div class="card">
                    <div class="card-label">Institutional Demo Capital</div>
                    <div id="acc-balance" class="card-value">$50,000.00</div>
                    <div class="card-sub">Initial Capital: $50,000.00</div>
                </div>
                <div class="card">
                    <div class="card-label">Total Portfolio Equity</div>
                    <div id="acc-equity" class="card-value" style="color: var(--accent-green);">$50,000.00</div>
                    <div id="acc-pnl" class="card-sub" style="color: var(--accent-green);">+$0.00 (+0.00%)</div>
                </div>
                <div class="card">
                    <div class="card-label">SMC Win-Rate & Trades</div>
                    <div id="acc-winrate" class="card-value">100.0%</div>
                    <div id="acc-trades" class="card-sub">0 Closed Trades</div>
                </div>
                <div class="card">
                    <div class="card-label">Bitcoin Market Price</div>
                    <div id="btc-price" class="card-value">$65,000.00</div>
                    <div id="btc-change" class="card-sub">+0.00% 24h</div>
                </div>
            </div>

            <!-- Second Row: SMC & Fibonacci Analysis & Active Orders -->
            <div class="grid-2">
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <span class="card-label" style="margin: 0;">Smart Money Concepts & Fibonacci Framework</span>
                        <span id="market-sync" style="font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono';">Syncing...</span>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
                        <div style="background: #090e17; padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--muted); margin-bottom: 4px;">HTF MARKET TREND</div>
                            <div id="htf-trend" style="font-size: 18px; font-weight: 800; color: var(--accent-green);">BULLISH</div>
                            <small id="struct-event" style="color: var(--muted);">Structure: Normal</small>
                        </div>
                        <div style="background: #090e17; padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--muted); margin-bottom: 4px;">EQUILIBRIUM ZONE (50%)</div>
                            <div id="zone-status" style="font-size: 16px; font-weight: 800; color: var(--accent-gold);">DISCOUNT ZONE</div>
                            <small id="eq-val" style="color: var(--muted);">Eq: $0.00</small>
                        </div>
                    </div>

                    <div style="background: #090e17; padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                        <div style="font-size: 11px; color: var(--muted); margin-bottom: 6px;">FIBONACCI GOLDEN POCKET (0.618 - 0.786 OTE)</div>
                        <div id="golden-pocket" style="font-size: 16px; font-weight: 700; color: var(--accent-blue); font-family: 'JetBrains Mono';">
                            $0.00 - $0.00
                        </div>
                        <div style="margin-top: 6px; font-size: 12px; color: var(--muted);">
                            Target 1 (Extension): <span id="tp-ext1" style="color: var(--accent-green);">$0.00</span> | 
                            Swing High: <span id="swing-h">$0.00</span> | Swing Low: <span id="swing-l">$0.00</span>
                        </div>
                    </div>

                    <h4 style="margin: 20px 0 10px 0; font-size: 14px; text-transform: uppercase; color: var(--muted);">Live Active SMC Paper Orders</h4>
                    <div style="overflow-x: auto;">
                        <table>
                            <thead>
                                <tr>
                                    <th>ID</th>
                                    <th>Symbol</th>
                                    <th>Side</th>
                                    <th>Entry</th>
                                    <th>Stop Loss</th>
                                    <th>Take Profit</th>
                                    <th>RRR</th>
                                    <th>Floating PnL</th>
                                </tr>
                            </thead>
                            <tbody id="open-trades-tbody">
                                <tr><td colspan="8" style="text-align: center; color: var(--muted);">Scanning for high-probability Golden Pocket mitigation...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Right Column: AI Social Media Agency & Lead Capture -->
                <div class="card">
                    <div class="card-label">AI Social Media Agency Engine</div>
                    <p style="font-size: 13px; color: var(--muted); margin-top: 0;">Autonomous content creator & inbound client qualification pipeline</p>
                    
                    <div id="social-container">
                        <div class="social-card">
                            <span class="tag tag-gold">Twitter Thread</span>
                            <p style="margin: 8px 0 0 0; color: #cbd5e1;">Generating algorithmic trade breakdowns and agency thought-leadership content...</p>
                        </div>
                    </div>

                    <h4 style="margin: 20px 0 10px 0; font-size: 14px; text-transform: uppercase; color: var(--muted);">Recent Inbound Client Inquiries</h4>
                    <div id="leads-container" style="max-height: 140px; overflow-y: auto;">
                        <p style="font-size: 12px; color: var(--muted);">Listening on API endpoint: <code>/api/lead</code></p>
                    </div>
                </div>
            </div>

            <!-- Bottom Console -->
            <div class="card" style="padding: 16px 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span class="card-label" style="margin: 0;">Institutional Event Stream & Multi-Agent Telemetry</span>
                    <span style="font-size: 11px; color: var(--muted);">24/7 Background Core</span>
                </div>
                <div class="terminal" id="terminal-logs">
                    <p>[CORE] Initializing institutional quantitative framework...</p>
                </div>
            </div>
        </div>

        <script>
            async function syncTelemetry() {
                try {
                    const res = await fetch('/api/telemetry');
                    const d = await res.json();

                    // Account Stats
                    document.getElementById('acc-balance').innerText = '$' + d.account.balance.toLocaleString('en-US', {minimumFractionDigits: 2});
                    document.getElementById('acc-equity').innerText = '$' + d.account.equity.toLocaleString('en-US', {minimumFractionDigits: 2});
                    
                    const pnlSign = d.account.total_pnl >= 0 ? '+' : '';
                    const pnlElem = document.getElementById('acc-pnl');
                    pnlElem.innerText = `${pnlSign}$${d.account.total_pnl.toFixed(2)} (${pnlSign}${d.account.pnl_percent}%)`;
                    pnlElem.style.color = d.account.total_pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';

                    document.getElementById('acc-winrate').innerText = d.account.win_rate + '%';
                    document.getElementById('acc-trades').innerText = `${d.account.closed_trades_count} Closed Trades | ${d.account.open_trades_count} Active`;

                    // Market Analysis
                    const m = d.market_analysis;
                    if (m && m.current_price) {
                        document.getElementById('btc-price').innerText = '$' + m.current_price.toLocaleString('en-US', {minimumFractionDigits: 2});
                        const chgSign = m.change_pct >= 0 ? '+' : '';
                        document.getElementById('btc-change').innerText = `${chgSign}${m.change_pct.toFixed(2)}% 24h`;
                        document.getElementById('btc-change').style.color = m.change_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';

                        document.getElementById('htf-trend').innerText = m.trend;
                        document.getElementById('htf-trend').style.color = m.trend === 'BULLISH' ? 'var(--accent-green)' : 'var(--accent-red)';
                        document.getElementById('struct-event').innerText = 'Event: ' + m.structure_event;

                        document.getElementById('zone-status').innerText = m.zone_status;
                        document.getElementById('zone-status').style.color = m.zone_status.includes('PRIME') ? 'var(--accent-green)' : 'var(--accent-gold)';

                        if (m.fib_levels && m.fib_levels.golden_pocket_ote) {
                            const ote = m.fib_levels.golden_pocket_ote;
                            document.getElementById('golden-pocket').innerText = `$${ote.low.toLocaleString()} - $${ote.high.toLocaleString()}`;
                            document.getElementById('eq-val').innerText = 'Eq: $' + m.fib_levels.equilibrium_50.toLocaleString();
                            document.getElementById('tp-ext1').innerText = '$' + m.fib_levels.target_ext_1.toLocaleString();
                            document.getElementById('swing-h').innerText = '$' + m.swing_high.toLocaleString();
                            document.getElementById('swing-l').innerText = '$' + m.swing_low.toLocaleString();
                        }
                        document.getElementById('market-sync').innerText = 'Last sync: ' + m.last_synced;
                    }

                    // Open Trades
                    const tbody = document.getElementById('open-trades-tbody');
                    if (d.open_trades.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--muted); padding: 18px;">Scanning 1H/4H candle structure for Golden Pocket order blocks...</td></tr>';
                    } else {
                        tbody.innerHTML = d.open_trades.map(t => {
                            const sideTag = t.side === 'BUY' ? 'tag-green' : 'tag-red';
                            const pnlColor = t.current_pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
                            const pnlSign = t.current_pnl >= 0 ? '+' : '';
                            return `
                                <tr>
                                    <td>${t.id}</td>
                                    <td><strong>${t.symbol}</strong></td>
                                    <td><span class="tag ${sideTag}">${t.side}</span></td>
                                    <td>$${t.entry_price.toLocaleString()}</td>
                                    <td style="color: var(--accent-red);">$${t.stop_loss.toLocaleString()}</td>
                                    <td style="color: var(--accent-green);">$${t.take_profit.toLocaleString()}</td>
                                    <td>1:${t.rrr}</td>
                                    <td style="color: ${pnlColor}; font-weight: 700;">${pnlSign}$${t.current_pnl.toFixed(2)}</td>
                                </tr>
                            `;
                        }).join('');
                    }

                    // Social Posts
                    if (d.social_posts && d.social_posts.length > 0) {
                        const sCont = document.getElementById('social-container');
                        sCont.innerHTML = d.social_posts.slice(0, 2).map(p => `
                            <div class="social-card">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                    <span class="tag tag-gold">${p.platform}</span>
                                    <span style="font-size: 11px; color: var(--muted);">${p.created_at}</span>
                                </div>
                                <div style="font-weight: 700; color: #fff; margin-bottom: 4px;">${p.topic}</div>
                                <div style="color: #cbd5e1; white-space: pre-line;">${p.content}</div>
                            </div>
                        `).join('');
                    }

                    // Logs
                    const logElem = document.getElementById('terminal-logs');
                    logElem.innerHTML = d.logs.map(l => `<p style="margin: 4px 0;">${l}</p>`).join('');
                } catch(e) {}
            }

            setInterval(syncTelemetry, 3500);
            syncTelemetry();
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 7860))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
