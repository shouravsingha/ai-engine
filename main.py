import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.orchestrator import MasterOrchestrator

app = FastAPI(title="Institutional SMC Quant Desk, Exness Bridge & AI Agency Engine")
orchestrator = MasterOrchestrator()

@app.on_event("startup")
def startup_event():
    orchestrator.start_background_loop()

@app.get("/api/telemetry")
def get_telemetry():
    return JSONResponse({
        "account": orchestrator.account.get_summary(),
        "exness": orchestrator.exness.get_status(),
        "open_trades": orchestrator.account.open_trades,
        "trade_history": orchestrator.account.trade_history[-10:],
        "market_analysis": orchestrator.last_analysis,
        "social_posts": orchestrator.social.get_recent_posts(),
        "leads": orchestrator.leads.get_leads(),
        "logs": orchestrator.system_logs
    })

class ExnessConnectInput(BaseModel):
    account_id: str
    server: Optional[str] = "Exness-MT5Trial"
    balance: Optional[float] = 50000.0

@app.post("/api/exness/connect")
def connect_exness(data: ExnessConnectInput):
    res = orchestrator.exness.connect_account(
        account_id=data.account_id,
        server=data.server,
        balance=data.balance
    )
    orchestrator.account.balance = data.balance
    orchestrator.account.equity = data.balance
    orchestrator.log(f"🔗 EXNESS DEMO CONNECTED: Account #{data.account_id} on {data.server} | Balance: ${data.balance:,.2f}")
    return {"status": "success", "exness": res}

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
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #06080e;
                --surface: #0e1320;
                --surface-hover: #151c2e;
                --border: #1a2338;
                --accent-blue: #38bdf8;
                --accent-green: #10b981;
                --accent-red: #f43f5e;
                --accent-gold: #f59e0b;
                --accent-purple: #a855f7;
                --text: #f8fafc;
                --muted: #94a3b8;
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                padding: 24px;
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Plus Jakarta Sans', sans-serif;
                -webkit-font-smoothing: antialiased;
            }
            .container { max-width: 1400px; margin: auto; }
            
            /* Header */
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: linear-gradient(135deg, rgba(14, 19, 32, 0.95), rgba(21, 28, 46, 0.8));
                backdrop-filter: blur(12px);
                padding: 22px 28px;
                border-radius: 16px;
                border: 1px solid var(--border);
                margin-bottom: 24px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            }
            .title-area h1 { margin: 0; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; display: flex; align-items: center; gap: 10px; }
            .title-area p { margin: 6px 0 0 0; color: var(--muted); font-size: 13.5px; }
            
            .header-badges { display: flex; align-items: center; gap: 12px; }
            .badge {
                padding: 7px 15px; border-radius: 30px; font-size: 12.5px; font-weight: 700;
                display: flex; align-items: center; gap: 8px; cursor: pointer; transition: all 0.2s;
            }
            .badge-live { background: rgba(16, 185, 129, 0.12); color: var(--accent-green); border: 1px solid rgba(16, 185, 129, 0.4); }
            .badge-exness { background: rgba(245, 158, 11, 0.12); color: var(--accent-gold); border: 1px solid rgba(245, 158, 11, 0.4); }
            .badge-exness:hover { background: rgba(245, 158, 11, 0.25); transform: translateY(-1px); }
            .pulse { width: 8px; height: 8px; border-radius: 50%; background: currentColor; box-shadow: 0 0 10px currentColor; animation: pulse 1.6s infinite; }
            @keyframes pulse { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }

            /* Navigation Tabs */
            .nav-tabs {
                display: flex;
                gap: 10px;
                margin-bottom: 24px;
                border-bottom: 1px solid var(--border);
                padding-bottom: 8px;
            }
            .tab-btn {
                background: transparent;
                border: none;
                color: var(--muted);
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 700;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .tab-btn.active {
                background: var(--surface);
                color: var(--accent-blue);
                border: 1px solid var(--border);
            }
            .tab-btn:hover:not(.active) { color: #fff; background: rgba(255,255,255,0.03); }

            /* Cards & Grid */
            .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }
            .grid-2 { display: grid; grid-template-columns: 1.25fr 0.75fr; gap: 20px; margin-bottom: 24px; }
            .card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 22px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            }
            .card-label { font-size: 11.5px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
            .card-value { font-size: 26px; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
            .card-sub { font-size: 13px; color: var(--muted); margin-top: 6px; }

            /* Tags */
            .tag { display: inline-block; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
            .tag-green { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
            .tag-red { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
            .tag-gold { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
            .tag-blue { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }

            /* Table */
            table { width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13px; }
            th { text-align: left; padding: 12px 14px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); }
            td { padding: 12px 14px; border-bottom: 1px solid #141b29; font-family: 'JetBrains Mono', monospace; }

            /* Terminal & Visual Explainer */
            .terminal {
                background: #04060a;
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 18px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 12.5px;
                height: 240px;
                overflow-y: auto;
                color: #38bdf8;
                line-height: 1.6;
            }
            .step-box {
                background: #090e18;
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 14px;
                display: flex;
                gap: 14px;
                align-items: flex-start;
            }
            .step-num {
                background: var(--accent-blue);
                color: #000;
                font-weight: 800;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
                font-size: 13px;
            }

            /* Modal */
            .modal-bg {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
                display: none; align-items: center; justify-content: center; z-index: 1000;
            }
            .modal-box {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 28px;
                width: 90%; max-width: 480px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            }
            .input-group { margin-bottom: 16px; }
            .input-group label { display: block; font-size: 12.5px; font-weight: 700; color: var(--muted); margin-bottom: 6px; }
            .input-group input, .input-group select {
                width: 100%; padding: 12px; border-radius: 8px; border: 1px solid var(--border);
                background: #070a12; color: #fff; font-family: inherit; font-size: 14px;
            }
            .btn-primary {
                width: 100%; padding: 12px; border-radius: 8px; border: none;
                background: var(--accent-blue); color: #000; font-weight: 700; font-size: 14px;
                cursor: pointer; transition: opacity 0.2s;
            }
            .btn-primary:hover { opacity: 0.9; }

            @media (max-width: 950px) { .grid-2 { grid-template-columns: 1fr; } .header { flex-direction: column; align-items: flex-start; gap: 16px; } }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- Header -->
            <div class="header">
                <div class="title-area">
                    <h1>🚀 Institutional SMC Desk & AI Agency</h1>
                    <p>High Timeframe (HTF) Trend Execution · Fibonacci OTE (0.618 - 0.786) · $50k Exness Paper Bridge</p>
                </div>
                <div class="header-badges">
                    <div class="badge badge-exness" onclick="openExnessModal()">
                        <div class="pulse"></div>
                        <span id="badge-exness-text">⚙️ Connect Exness Demo</span>
                    </div>
                    <div class="badge badge-live">
                        <div class="pulse"></div>
                        <span>24/7 ONLINE</span>
                    </div>
                </div>
            </div>

            <!-- Navigation Tabs -->
            <div class="nav-tabs">
                <button class="tab-btn active" onclick="switchTab('trading')">📊 Trading Desk</button>
                <button class="tab-btn" onclick="switchTab('agency')">🏢 AI Agency Hub</button>
                <button class="tab-btn" onclick="switchTab('explainer')">💡 How The System Works</button>
            </div>

            <!-- TAB 1: TRADING DESK -->
            <div id="tab-trading">
                <!-- Top Metrics -->
                <div class="grid-4">
                    <div class="card">
                        <div class="card-label">Exness Demo Balance</div>
                        <div id="acc-balance" class="card-value">$50,000.00</div>
                        <div id="exness-server-sub" class="card-sub">Server: Exness-MT5Trial</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Total Portfolio Equity</div>
                        <div id="acc-equity" class="card-value" style="color: var(--accent-green);">$50,000.00</div>
                        <div id="acc-pnl" class="card-sub" style="color: var(--accent-green);">+$0.00 (+0.00%)</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Win-Rate & Execution</div>
                        <div id="acc-winrate" class="card-value">100.0%</div>
                        <div id="acc-trades" class="card-sub">0 Closed Trades | 0 Active</div>
                    </div>
                    <div class="card">
                        <div class="card-label">Bitcoin Market Price</div>
                        <div id="btc-price" class="card-value">$65,000.00</div>
                        <div id="btc-change" class="card-sub">+0.00% 24h</div>
                    </div>
                </div>

                <!-- SMC Engine & Active Orders -->
                <div class="grid-2">
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                            <span class="card-label" style="margin: 0;">Smart Money Concepts & Fibonacci Framework</span>
                            <span id="market-sync" style="font-size: 11px; color: var(--muted); font-family: 'JetBrains Mono';">Syncing...</span>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-bottom: 16px;">
                            <div style="background: #080c14; padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                                <div style="font-size: 11px; color: var(--muted); margin-bottom: 4px;">HTF MARKET TREND</div>
                                <div id="htf-trend" style="font-size: 18px; font-weight: 800; color: var(--accent-green);">BULLISH</div>
                                <small id="struct-event" style="color: var(--muted);">Structure: Normal</small>
                            </div>
                            <div style="background: #080c14; padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                                <div style="font-size: 11px; color: var(--muted); margin-bottom: 4px;">EQUILIBRIUM ZONE (50%)</div>
                                <div id="zone-status" style="font-size: 15px; font-weight: 800; color: var(--accent-gold);">DISCOUNT ZONE</div>
                                <small id="eq-val" style="color: var(--muted);">Eq: $0.00</small>
                            </div>
                        </div>

                        <div style="background: #080c14; padding: 14px; border-radius: 10px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--muted); margin-bottom: 6px;">FIBONACCI GOLDEN POCKET (0.618 - 0.786 OTE)</div>
                            <div id="golden-pocket" style="font-size: 16px; font-weight: 700; color: var(--accent-blue); font-family: 'JetBrains Mono';">
                                $0.00 - $0.00
                            </div>
                            <div style="margin-top: 6px; font-size: 12px; color: var(--muted);">
                                Target 1 (Extension): <span id="tp-ext1" style="color: var(--accent-green);">$0.00</span> | 
                                Swing High: <span id="swing-h">$0.00</span> | Swing Low: <span id="swing-l">$0.00</span>
                            </div>
                        </div>

                        <h4 style="margin: 20px 0 10px 0; font-size: 13.5px; text-transform: uppercase; color: var(--muted);">Live Active SMC Paper Orders</h4>
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
                                    <tr><td colspan="8" style="text-align: center; color: var(--muted); padding: 18px;">Scanning 1H/4H candle structure for Golden Pocket order blocks...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Exness Bridge Card -->
                    <div class="card">
                        <div class="card-label">Exness Demo Bridge & Execution</div>
                        <p style="font-size: 13px; color: var(--muted); margin-top: 0;">Synchronizes trades directly with MetaTrader 5 (Exness-MT5Trial)</p>
                        
                        <div style="background: #080c14; border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 16px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-size: 13px; color: var(--muted);">Bridge Status:</span>
                                <span id="exness-status-tag" class="tag tag-gold">STANDBY</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-size: 13px; color: var(--muted);">Account ID:</span>
                                <strong id="exness-acc-id" style="font-family: 'JetBrains Mono';">Not Connected</strong>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="font-size: 13px; color: var(--muted);">Server:</span>
                                <span id="exness-server-name">Exness-MT5Trial</span>
                            </div>
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-size: 13px; color: var(--muted);">Leverage:</span>
                                <span>1:200</span>
                            </div>
                        </div>

                        <button class="btn-primary" onclick="openExnessModal()">🔗 Connect / Edit Exness Demo Account</button>

                        <h4 style="margin: 22px 0 10px 0; font-size: 13px; text-transform: uppercase; color: var(--muted);">Recent Settled Trades</h4>
                        <div id="history-container" style="max-height: 150px; overflow-y: auto; font-size: 12.5px;">
                            <p style="color: var(--muted);">No closed trades yet.</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- TAB 2: AI AGENCY HUB -->
            <div id="tab-agency" style="display: none;">
                <div class="grid-2">
                    <div class="card">
                        <div class="card-label">AI Social Media Content Queue</div>
                        <p style="font-size: 13px; color: var(--muted); margin-top: 0;">Autonomous posts generated for Twitter/X and LinkedIn to build audience and agency authority</p>
                        <div id="social-container"></div>
                    </div>
                    <div class="card">
                        <div class="card-label">Client Lead Onboarding Pipeline</div>
                        <p style="font-size: 13px; color: var(--muted); margin-top: 0;">Incoming leads scored and categorized into service proposals automatically</p>
                        <div id="leads-container" style="max-height: 380px; overflow-y: auto;"></div>
                    </div>
                </div>
            </div>

            <!-- TAB 3: HOW THE SYSTEM WORKS (EXPLAINER) -->
            <div id="tab-explainer" style="display: none;">
                <div class="card" style="max-width: 900px; margin: auto;">
                    <h2 style="margin-top: 0; color: var(--accent-blue);">🧠 How The Institutional SMC & Fibonacci Engine Operates</h2>
                    <p style="color: var(--muted); line-height: 1.6;">
                        Anyone viewing this system can easily understand how our quantitative algorithms eliminate emotions and trade like institutional market makers:
                    </p>

                    <div class="step-box">
                        <div class="step-num">1</div>
                        <div>
                            <h4 style="margin: 0 0 4px 0; color: #fff;">High Time Frame (HTF) Trend Direction</h4>
                            <p style="margin: 0; font-size: 13px; color: var(--muted); line-height: 1.5;">
                                The bot evaluates 4H and 1H candles. If the market is printing Higher Highs (HH) and Higher Lows (HL), the trend is <strong>BULLISH</strong>. In a bullish trend, the bot <strong>ONLY buys (Long)</strong> and never shorts. In a bearish trend, it <strong>ONLY sells (Short)</strong>.
                            </p>
                        </div>
                    </div>

                    <div class="step-box">
                        <div class="step-num">2</div>
                        <div>
                            <h4 style="margin: 0 0 4px 0; color: #fff;">50% Equilibrium (Discount vs. Premium Zone)</h4>
                            <p style="margin: 0; font-size: 13px; color: var(--muted); line-height: 1.5;">
                                Retail traders buy when prices are expensive. Institutions buy wholesale. The algorithm divides the swing into two halves. It will <strong>ONLY enter buy orders in the Discount Zone (&lt;50% of the move)</strong>.
                            </p>
                        </div>
                    </div>

                    <div class="step-box">
                        <div class="step-num">3</div>
                        <div>
                            <h4 style="margin: 0 0 4px 0; color: #fff;">Fibonacci Golden Pocket (0.618 - 0.786 OTE)</h4>
                            <p style="margin: 0; font-size: 13px; color: var(--muted); line-height: 1.5;">
                                The prime mathematical entry point. When price pulls back into the 0.618 to 0.786 Fibonacci retracement zone and meets an <strong>Order Block (OB)</strong> or <strong>Fair Value Gap (FVG)</strong>, the high-probability trigger is primed.
                            </p>
                        </div>
                    </div>

                    <div class="step-box">
                        <div class="step-num">4</div>
                        <div>
                            <h4 style="margin: 0 0 4px 0; color: #fff;">Chief Risk Officer (Strict 1% Capital Defense)</h4>
                            <p style="margin: 0; font-size: 13px; color: var(--muted); line-height: 1.5;">
                                No trade is allowed to risk more than <strong>1.0% ($500 on $50k)</strong>. The system calculates exact position sizing based on the distance between Entry and Stop Loss. The minimum Risk-Reward Ratio (RRR) must be <strong>1:2.5 or higher</strong>.
                            </p>
                        </div>
                    </div>

                    <div class="step-box">
                        <div class="step-num">5</div>
                        <div>
                            <h4 style="margin: 0 0 4px 0; color: #fff;">Exness Bridge & Real-Time Settlement</h4>
                            <p style="margin: 0; font-size: 13px; color: var(--muted); line-height: 1.5;">
                                The order is simultaneously logged to the internal equity curve and forwarded to the Exness Demo Bridge. Floating PnL is tracked tick-by-tick until Take Profit or Stop Loss is met.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Bottom Console -->
            <div class="card" style="padding: 16px 20px; margin-top: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span class="card-label" style="margin: 0;">Institutional Event Stream & Live Telemetry</span>
                    <span style="font-size: 11px; color: var(--muted);">24/7 Autonomous Core</span>
                </div>
                <div class="terminal" id="terminal-logs">
                    <p>[CORE] Initializing institutional quantitative framework...</p>
                </div>
            </div>
        </div>

        <!-- EXNESS CONNECTION MODAL -->
        <div id="exness-modal" class="modal-bg">
            <div class="modal-box">
                <h3 style="margin-top: 0; color: #fff;">⚙️ Connect Exness Demo Account</h3>
                <p style="font-size: 13px; color: var(--muted);">Enter your Exness MetaTrader 5 demo account credentials to link with the algorithmic desk.</p>
                
                <div class="input-group">
                    <label>Exness Account Number (Login ID)</label>
                    <input type="text" id="modal-acc-id" placeholder="e.g. 142859102">
                </div>
                <div class="input-group">
                    <label>Server</label>
                    <select id="modal-server">
                        <option value="Exness-MT5Trial">Exness-MT5Trial</option>
                        <option value="Exness-MT5Trial2">Exness-MT5Trial2</option>
                        <option value="Exness-MT5Trial9">Exness-MT5Trial9</option>
                        <option value="Exness-MT4Trial">Exness-MT4Trial</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>Initial Demo Balance (USD)</label>
                    <input type="number" id="modal-balance" value="50000">
                </div>

                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button class="btn-primary" onclick="submitExnessConnect()">Save & Link Account</button>
                    <button class="tab-btn" onclick="closeExnessModal()" style="border: 1px solid var(--border);">Cancel</button>
                </div>
            </div>
        </div>

        <script>
            function switchTab(tab) {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.getElementById('tab-trading').style.display = 'none';
                document.getElementById('tab-agency').style.display = 'none';
                document.getElementById('tab-explainer').style.display = 'none';

                if (tab === 'trading') {
                    document.getElementById('tab-trading').style.display = 'block';
                    event.target.classList.add('active');
                } else if (tab === 'agency') {
                    document.getElementById('tab-agency').style.display = 'block';
                    event.target.classList.add('active');
                } else if (tab === 'explainer') {
                    document.getElementById('tab-explainer').style.display = 'block';
                    event.target.classList.add('active');
                }
            }

            function openExnessModal() {
                document.getElementById('exness-modal').style.display = 'flex';
            }
            function closeExnessModal() {
                document.getElementById('exness-modal').style.display = 'none';
            }

            async function submitExnessConnect() {
                const accId = document.getElementById('modal-acc-id').value;
                const server = document.getElementById('modal-server').value;
                const bal = parseFloat(document.getElementById('modal-balance').value) || 50000;

                if (!accId) {
                    alert('Please enter your Exness Account Number');
                    return;
                }

                try {
                    const res = await fetch('/api/exness/connect', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ account_id: accId, server: server, balance: bal })
                    });
                    const data = await res.json();
                    closeExnessModal();
                    syncTelemetry();
                } catch(e) {
                    alert('Error connecting Exness account.');
                }
            }

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
                    document.getElementById('acc-trades').innerText = `${d.account.closed_trades_count} Closed | ${d.account.open_trades_count} Active`;

                    // Exness Status
                    const ex = d.exness;
                    if (ex && ex.connected) {
                        document.getElementById('badge-exness-text').innerText = `🔗 Connected: #${ex.account_id}`;
                        document.getElementById('exness-status-tag').innerText = 'CONNECTED';
                        document.getElementById('exness-status-tag').className = 'tag tag-green';
                        document.getElementById('exness-acc-id').innerText = '#' + ex.account_id;
                        document.getElementById('exness-server-name').innerText = ex.server;
                        document.getElementById('exness-server-sub').innerText = `Exness: ${ex.server} (#${ex.account_id})`;
                    } else {
                        document.getElementById('badge-exness-text').innerText = '⚙️ Connect Exness Demo';
                        document.getElementById('exness-status-tag').innerText = 'STANDBY';
                        document.getElementById('exness-status-tag').className = 'tag tag-gold';
                    }

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

                    // Open Trades Table
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

                    // Trade History
                    const histElem = document.getElementById('history-container');
                    if (d.trade_history && d.trade_history.length > 0) {
                        histElem.innerHTML = d.trade_history.map(th => `
                            <div style="display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid #161e2e;">
                                <span>${th.id} (${th.side})</span>
                                <span style="color:${th.realized_pnl >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'}">
                                    ${th.realized_pnl >= 0 ? '+' : ''}$${th.realized_pnl.toFixed(2)}
                                </span>
                            </div>
                        `).join('');
                    }

                    // Social Posts Tab
                    if (d.social_posts && d.social_posts.length > 0) {
                        document.getElementById('social-container').innerHTML = d.social_posts.map(p => `
                            <div style="background:#080c14; border:1px solid var(--border); border-radius:10px; padding:16px; margin-bottom:14px;">
                                <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                                    <span class="tag tag-gold">${p.platform}</span>
                                    <span style="font-size:11px; color:var(--muted);">${p.created_at}</span>
                                </div>
                                <div style="font-weight:700; color:#fff; margin-bottom:6px;">${p.topic}</div>
                                <div style="color:#cbd5e1; font-size:13px; line-height:1.5; white-space:pre-line;">${p.content}</div>
                            </div>
                        `).join('');
                    }

                    // Leads Tab
                    if (d.leads && d.leads.length > 0) {
                        document.getElementById('leads-container').innerHTML = d.leads.map(l => `
                            <div style="background:#080c14; border:1px solid var(--border); border-radius:10px; padding:14px; margin-bottom:12px;">
                                <div style="display:flex; justify-content:space-between;">
                                    <strong>${l.name} (${l.company})</strong>
                                    <span class="tag tag-blue">Score: ${l.score}</span>
                                </div>
                                <p style="font-size:12px; color:var(--muted); margin:4px 0;">Tier: ${l.tier} | Budget: ${l.budget}</p>
                            </div>
                        `).join('');
                    }

                    // Terminal Logs
                    document.getElementById('terminal-logs').innerHTML = d.logs.map(l => `<p style="margin: 4px 0;">${l}</p>`).join('');
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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
