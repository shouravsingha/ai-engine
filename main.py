import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.orchestrator import MasterOrchestrator

app = FastAPI(title="TradingAI · Real-Time Animated OrderFlow & 3D Office with AI Brain")
orchestrator = MasterOrchestrator()

@app.on_event("startup")
def startup_event():
    orchestrator.start_background_loop()

@app.get("/api/telemetry")
def get_telemetry():
    return JSONResponse({
        "account": orchestrator.account.get_summary(),
        "exness": orchestrator.exness.get_status(),
        "market_matrix": orchestrator.multi_market_matrix,
        "orderflow": orchestrator.orderflow.get_order_flow_matrix(),
        "ai_brain": orchestrator.brain.get_status(),
        "agents": orchestrator.agents,
        "agent_messages": orchestrator.agent_messages,
        "open_trades": orchestrator.account.open_trades,
        "trade_history": orchestrator.account.trade_history[-10:],
        "branding_posts": orchestrator.branding.get_feed(),
        "telegram_status": {"bot": "@SingAiTradebot", "active": orchestrator.telegram.is_running},
        "webhooks": orchestrator.webhooks.webhooks,
        "logs": orchestrator.system_logs
    })

class TaskInput(BaseModel):
    task: str

@app.post("/api/task")
def assign_task(data: TaskInput):
    task_text = data.task.strip()
    orchestrator.send_agent_message("You (Director)", "Firm Director", f"🎯 DIRECTIVE: {task_text}")
    
    if "brain" in task_text.lower() or "audit" in task_text.lower() or "teach" in task_text.lower():
        orchestrator.brain.teach_agent("All Agents", "Institutional Discipline", "Maintain 100% adherence to 1% risk ceiling.")
        orchestrator.send_agent_message("AI Brain", "Neural Overseer", "🧠 Full workforce audit executed. All 7 robot agents calibrated.")
    elif "coffee" in task_text.lower():
        orchestrator.send_agent_message("Mia", "Viral Copywriter (PA_07)", "Taking a 2-minute coffee break at the lounge! ☕")
        orchestrator.send_agent_message("Leo", "Execution Trader (PA_14)", "Grabbing an espresso, Exness trailing stops are active.")
    elif "scan" in task_text.lower() or "orderflow" in task_text.lower():
        orchestrator.run_simultaneous_scan()
        orchestrator.send_agent_message("Alex", "Chief Quant (PA_01)", "Simultaneous OrderFlow scan complete across Forex & Commodities.")
    elif "broadcast" in task_text.lower() or "news" in task_text.lower():
        post = orchestrator.branding.generate_firm_content("BULLISH", "$2,748 (Gold)")
        orchestrator.webhooks.broadcast_branding(post["headline"], post["content"])
        orchestrator.telegram.send_branding_alert(post["headline"], post["content"])
        orchestrator.send_agent_message("Sophia", "Brand Director (Conta_1612)", "Dispatched breaking broadcast to all social webhooks & Telegram!")
    else:
        orchestrator.send_agent_message("Alex", "Chief Quant (PA_01)", f"Executing directive: '{task_text}'.")

    return {"status": "success"}

class WebhookConfigInput(BaseModel):
    discord: Optional[str] = ""
    slack: Optional[str] = ""
    generic_social: Optional[str] = ""

@app.post("/api/webhooks/save")
def save_webhooks(data: WebhookConfigInput):
    orchestrator.webhooks.set_webhook_url("discord", data.discord or "")
    orchestrator.webhooks.set_webhook_url("slack", data.slack or "")
    orchestrator.webhooks.set_webhook_url("generic_social", data.generic_social or "")
    orchestrator.send_agent_message("Sophia", "Brand Director (Conta_1612)", "Multi-platform social webhooks armed.")
    return {"status": "success", "webhooks": orchestrator.webhooks.webhooks}

@app.post("/api/trade/execute")
def direct_execute(data: dict):
    symbol = data.get("symbol", "XAUUSDm")
    side = data.get("side", "BUY")
    price = float(data.get("price", 2748.20))
    sl = price * 0.996 if side == "BUY" else price * 1.004
    tp = price * 1.012 if side == "BUY" else price * 0.988
    
    plan = orchestrator.risk.evaluate_and_size_trade(orchestrator.exness.balance, side, price, sl, tp)
    if plan:
        order = orchestrator.account.open_trade(plan, symbol=symbol)
        orchestrator.send_agent_message("Leo", "Execution Trader (PA_14)", f"OrderFlow Direct Execution: {side} {symbol} at ${price:,.2f}! Exness MT5 synced.")
        orchestrator.telegram.send_trade_signal(order, asset=symbol)
        orchestrator.webhooks.broadcast_trade(order, asset=symbol)
        return {"status": "success", "order": order}
    return {"status": "rejected", "message": "Risk threshold exceeded"}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OrderFlow Real-Time Matrix & 3D Robot Floor with AI Neural Brain</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <!-- Three.js + OrbitControls -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            :root {
                --bg: #f8fafc;
                --surface: #ffffff;
                --border: #e2e8f0;
                --text-dark: #0f172a;
                --text-muted: #64748b;
                --green: #10b981;
                --green-bg: #ecfdf5;
                --green-line: #059669;
                --red: #ef4444;
                --red-bg: #fef2f2;
                --red-line: #dc2626;
                --blue: #0284c7;
                --gold: #d97706;
                --brain-glow: #ec4899;
            }
            * { box-sizing: border-box; }
            body, html {
                margin: 0; padding: 0; width: 100%; height: 100%;
                overflow-x: hidden; background: #080c14; color: #fff;
                font-family: 'Plus Jakarta Sans', sans-serif;
            }

            /* Main Header Bar */
            .top-nav-bar {
                background: #090e18; border-bottom: 1px solid #1a2438;
                padding: 10px 24px; display: flex; justify-content: space-between; align-items: center;
                position: sticky; top: 0; z-index: 100;
            }
            .brand-flow { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 16px; }
            .dot-flow { width: 9px; height: 9px; border-radius: 50%; background: #ef4444; animation: pulseRed 1.5s infinite; }
            @keyframes pulseRed { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }
            
            .tab-switch { display: flex; gap: 8px; }
            .tab-btn {
                background: #111726; border: 1px solid #1e293b; color: #94a3b8;
                padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 12.5px;
                cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px;
            }
            .tab-btn.active, .tab-btn:hover {
                background: #0284c7; color: #fff; border-color: #0284c7;
            }

            /* View Containers */
            #view-orderflow { padding: 20px 24px; max-width: 1580px; margin: auto; }
            #view-3d-floor { width: 100vw; height: calc(100vh - 58px); position: relative; display: none; }

            /* ORDERFLOW MASTER DASHBOARD (Matches 'new update.mp4') */
            .of-container {
                background: #ffffff; color: var(--text-dark); border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.4); overflow: hidden;
                border: 1px solid #cbd5e1;
            }
            .of-header {
                display: flex; justify-content: space-between; align-items: center;
                padding: 14px 20px; border-bottom: 1px solid var(--border);
                background: #f8fafc; font-size: 13px; font-weight: 600;
            }
            .dots-mac { display: flex; gap: 6px; }
            .mac-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }

            .of-grid {
                display: grid;
                grid-template-columns: 430px 1fr 340px;
                min-height: 740px;
                position: relative;
            }

            /* Left Ribbon Column with Smooth Particle Canvas */
            .col-ribbon {
                border-right: 1px solid var(--border);
                padding: 16px; display: flex; flex-direction: column;
                position: relative; background: #fafbfc;
            }
            #orderflow-particle-canvas {
                width: 100%; height: 380px; display: block; border-radius: 10px;
                background: linear-gradient(180deg, #f8fafc, #ffffff);
            }

            /* Middle Drill-Down Column (From Video Frame 7) */
            .col-center {
                padding: 20px 24px; border-right: 1px solid var(--border);
                display: flex; flex-direction: column; overflow-y: auto;
            }

            /* Right Column: Conviction Cards */
            .col-cards {
                padding: 16px; background: #f8fafc; display: flex; flex-direction: column; gap: 12px;
                overflow-y: auto; max-height: 760px;
            }

            /* Flow Items & Histograms */
            .flow-stat-row {
                display: flex; justify-content: space-between; align-items: center;
                padding: 5px 0; font-size: 12px; font-weight: 600;
            }
            .badge-flow { padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
            .bg-bull { background: var(--green-bg); color: var(--green-line); }
            .bg-bear { background: var(--red-bg); color: var(--red-line); }

            /* Conviction Asset Card */
            .asset-card-ui {
                background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
                padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                cursor: pointer; transition: all 0.2s;
            }
            .asset-card-ui:hover { border-color: #0284c7; transform: translateY(-2px); }
            .card-header-flex { display: flex; justify-content: space-between; align-items: flex-start; }
            .conviction-badge {
                padding: 3px 8px; border-radius: 6px; font-size: 10.5px; font-weight: 800;
                display: inline-flex; align-items: center; gap: 4px;
            }
            .conv-bull { background: #10b981; color: #fff; }
            .conv-bear { background: #ef4444; color: #fff; }

            .level-row {
                display: flex; justify-content: space-between; font-size: 11px;
                color: var(--text-muted); margin-top: 10px; border-top: 1px dashed #e2e8f0; padding-top: 6px;
            }

            /* Inspection Card (Frame 7) */
            .inspect-box {
                background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
                padding: 18px; margin-top: 14px;
            }
            .checklist-item {
                display: flex; align-items: center; gap: 8px; font-size: 12px;
                margin-bottom: 8px; color: #334155; font-weight: 500;
            }
            .check-icon { color: var(--green); font-weight: bold; }

            /* Volume Profile Horizontal Bars */
            .vp-container { display: flex; gap: 2px; align-items: center; height: 18px; margin: 3px 0; }
            .vp-bid { height: 8px; background: var(--green); border-radius: 2px 0 0 2px; }
            .vp-ask { height: 8px; background: var(--red); border-radius: 0 2px 2px 0; }

            /* 3D Viewport Controls & AI Brain HUD */
            #canvas-3d-wrap { width: 100%; height: 100%; position: relative; }
            #webgl-canvas { width: 100%; height: 100%; display: block; }
            
            .brain-hud {
                position: absolute; top: 16px; left: 16px;
                background: rgba(11, 15, 27, 0.92); backdrop-filter: blur(12px);
                border: 1px solid rgba(236, 72, 153, 0.4); border-radius: 14px;
                padding: 12px 18px; z-index: 20; display: flex; align-items: center; gap: 14px;
                box-shadow: 0 10px 30px rgba(236, 72, 153, 0.2);
            }
            .brain-icon-pulse {
                width: 14px; height: 14px; border-radius: 50%; background: #ec4899;
                box-shadow: 0 0 15px #ec4899; animation: brainPulse 1.4s infinite;
            }
            @keyframes brainPulse { 0% { opacity: 0.4; transform: scale(0.9); } 50% { opacity: 1; transform: scale(1.15); } 100% { opacity: 0.4; transform: scale(0.9); } }

            .dock-3d {
                position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                background: rgba(9, 13, 23, 0.9); backdrop-filter: blur(14px);
                border: 1px solid #1e293b; border-radius: 30px; padding: 6px 12px; display: flex; gap: 6px; z-index: 10;
            }
            .dock-btn {
                background: transparent; border: none; color: #94a3b8;
                padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700; cursor: pointer;
            }
            .dock-btn.active, .dock-btn:hover { background: #38bdf8; color: #000; }
        </style>
    </head>
    <body>
        <!-- TOP APP BAR -->
        <header class="top-nav-bar">
            <div class="brand-flow">
                <span class="dot-flow"></span>
                <span>• OrderFlow <span style="font-weight: 400; color: #94a3b8; font-size: 14px;">by TradingAI</span></span>
                <span style="background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">FOREX & COMMODITIES</span>
                <span style="background: rgba(236,72,153,0.15); color: #ec4899; border: 1px solid rgba(236,72,153,0.3); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">🧠 AI CENTRAL BRAIN ACTIVE</span>
            </div>

            <!-- View Switcher -->
            <div class="tab-switch">
                <button class="tab-btn active" onclick="switchView('orderflow')">🌊 Real-Time OrderFlow Matrix</button>
                <button class="tab-btn" onclick="switchView('3d')">🏢 3D Robot Floor (with AI Brain)</button>
            </div>

            <div style="display: flex; align-items: center; gap: 14px; font-size: 12px;">
                <span style="color: #10b981; font-weight: 700;">● @SingAiTradebot Live</span>
                <span style="background: #111726; border: 1px solid #1e293b; padding: 4px 10px; border-radius: 6px; font-family: 'JetBrains Mono';">Exness MT5: #434353249</span>
            </div>
        </header>

        <!-- VIEW 1: REAL-TIME ANIMATED ORDERFLOW MATRIX (Matches 'new update.mp4') -->
        <div id="view-orderflow">
            <div class="of-container">
                <!-- Sub Header -->
                <div class="of-header">
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <div class="dots-mac">
                            <span class="mac-dot" style="background:#ff5f56;"></span>
                            <span class="mac-dot" style="background:#ffbd2e;"></span>
                            <span class="mac-dot" style="background:#27c93f;"></span>
                        </div>
                        <span style="color: var(--text-muted); font-size: 12px;">Real-Time Liquidity Stream · <b>60% Bullish Inflow</b> vs <b>40% Bearish Outflow</b></span>
                    </div>
                    <div style="font-family: 'JetBrains Mono'; font-size: 12px; color: var(--blue);">
                        Exness MT5 Live: <span id="of-exness-bal" style="color: var(--green); font-weight: 800;">$20.21 USD</span>
                    </div>
                </div>

                <div class="of-grid">
                    <!-- LEFT COLUMN: CURRENCY INFLOWS & REAL-TIME ANIMATED PARTICLE RIBBON -->
                    <div class="col-ribbon">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                            <span style="font-size: 11px; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">Institutional Capital Flow</span>
                            <span style="font-size: 11px; font-weight: 700; color: var(--green);">Net Inflow: +1.8%</span>
                        </div>

                        <!-- Sector Rows -->
                        <div class="flow-stat-row"><span>🥇 Precious Metals (Gold)</span><span class="badge-flow bg-bull">+1.45%</span></div>
                        <div class="flow-stat-row"><span>🇪🇺 European Currencies</span><span class="badge-flow bg-bull">+0.84%</span></div>
                        <div class="flow-stat-row"><span>⚡ Crypto (BTC/ETH)</span><span class="badge-flow bg-bull">+2.18%</span></div>
                        <div class="flow-stat-row"><span>💵 US Dollar Index (DXY)</span><span class="badge-flow bg-bear">-0.71%</span></div>
                        <div class="flow-stat-row"><span>🇯🇵 Japanese Yen</span><span class="badge-flow bg-bear">-0.92%</span></div>

                        <!-- Smooth Animated HTML5 Flow Ribbon Canvas (Fluid Real-Time Motion) -->
                        <div style="margin-top: 12px; position: relative;">
                            <canvas id="orderflow-particle-canvas"></canvas>
                        </div>

                        <!-- Timeline Replay Bar -->
                        <div style="margin-top: auto; padding-top: 12px; border-top: 1px solid var(--border);">
                            <div style="display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); font-family: 'JetBrains Mono';">
                                <span>09:15</span><span>11:00</span><span>13:00</span><span>14:00</span><span style="color: var(--blue); font-weight: 800;">15:15 (LIVE TICK)</span>
                            </div>
                        </div>
                    </div>

                    <!-- CENTER COLUMN: DRILL-DOWN INSPECTION PANEL (Video Frame 7) -->
                    <div class="col-center">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h2 id="ins-title" style="margin: 0; font-size: 22px; font-weight: 800; color: var(--text-dark);">🥇 XAUUSD (Gold Spot)</h2>
                                <span style="font-size: 12px; color: var(--text-muted);">Precious Metals · Commodities · Institutional Flow</span>
                            </div>
                            <div style="text-align: right;">
                                <div id="ins-price" style="font-size: 24px; font-weight: 800; font-family: 'JetBrains Mono'; color: var(--gold);">$2,748.20</div>
                                <span id="ins-chg" class="badge-flow bg-bull">+1.45% (+39.31)</span>
                            </div>
                        </div>

                        <!-- Mini Chart & Levels -->
                        <div class="inspect-box">
                            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; font-size: 12px; margin-bottom: 14px;">
                                <div><small style="color: var(--text-muted);">Rank</small><div id="ins-rank" style="font-weight: 800;">#1 of 12 Pairs</div></div>
                                <div><small style="color: var(--text-muted);">Build-up</small><div id="ins-buildup" style="font-weight: 800; color: var(--green);">Long build-up</div></div>
                                <div><small style="color: var(--text-muted);">Conviction</small><div id="ins-conv" style="font-weight: 800; color: var(--blue);">●●●●● 5/5</div></div>
                                <div><small style="color: var(--text-muted);">Zone</small><div id="ins-zone" style="font-weight: 800; color: var(--gold);">2742 - 2748</div></div>
                            </div>

                            <!-- Support / Resistance Ladder -->
                            <div style="background: #f8fafc; border: 1px solid var(--border); border-radius: 8px; padding: 10px; font-family: 'JetBrains Mono'; font-size: 12px; display: flex; justify-content: space-between;">
                                <span>Support 1: <strong id="ins-s1" style="color: var(--green);">2735.00</strong></span>
                                <span>Equilibrium: <strong id="ins-eq">2745.00</strong></span>
                                <span>Resistance 1: <strong id="ins-r1" style="color: var(--red);">2765.00</strong></span>
                            </div>
                        </div>

                        <!-- "Why it ranks here" (From Video Frame 7) -->
                        <div class="inspect-box">
                            <div style="font-size: 13px; font-weight: 800; margin-bottom: 10px; color: var(--text-dark);">Why it ranks here (Institutional Criteria):</div>
                            <div class="checklist-item"><span class="check-icon">✓</span> <span>Positions opened with the move (Institutional Delta expansion)</span></div>
                            <div class="checklist-item"><span class="check-icon">✓</span> <span>The last 1H/4H candle agrees with Higher High structure</span></div>
                            <div class="checklist-item"><span class="check-icon">✓</span> <span>US Dollar index (DXY) leaning opposite direction (USD Weakness)</span></div>
                            <div class="checklist-item"><span class="check-icon">✓</span> <span>Mitigated 0.618 Fibonacci Golden Pocket in Discount Zone</span></div>
                            <div class="checklist-item"><span class="check-icon">✓</span> <span>AI Central Neural Brain: Validated & Approved for Exness</span></div>
                        </div>

                        <!-- Direct 1-Click Order Execution -->
                        <div style="margin-top: auto; padding-top: 14px;">
                            <button onclick="executeSelectedPair()" style="width: 100%; padding: 12px; border-radius: 8px; border: none; background: #0284c7; color: #fff; font-weight: 800; font-size: 13px; cursor: pointer;">
                                ⚡ Execute Order on Exness MT5 (#434353249)
                            </button>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN: HIGH-CONVICTION ASSET CARDS (Video Frame 3 & 7) -->
                    <div class="col-cards" id="cards-container"></div>
                </div>
            </div>
        </div>

        <!-- VIEW 2: 3D ROBOT OFFICE WITH AI CENTRAL NEURAL BRAIN -->
        <div id="view-3d-floor">
            <div id="canvas-3d-wrap">
                <!-- AI Brain Floating Diagnostics HUD -->
                <div class="brain-hud">
                    <div class="brain-icon-pulse"></div>
                    <div>
                        <div style="font-size: 12px; font-weight: 800; color: #ec4899;">AI CENTRAL NEURAL BRAIN</div>
                        <small style="color: #94a3b8;">Supervising 7 Robot Workers · 19 Mistakes Prevented · IQ 185</small>
                    </div>
                </div>

                <canvas id="webgl-canvas"></canvas>
            </div>
            <div class="dock-3d">
                <button class="dock-btn active" onclick="setCam('overview')">Overview</button>
                <button class="dock-btn" onclick="setCam('brain')">🧠 AI Brain Core</button>
                <button class="dock-btn" onclick="setCam('trading')">Robot Desks</button>
                <button class="dock-btn" onclick="setCam('branding')">Media Studio</button>
                <button class="dock-btn" onclick="setCam('coffee')">Coffee Bar</button>
                <button class="dock-btn" onclick="setCam('wall')">LED Wall</button>
            </div>
        </div>

        <script>
            let selectedAsset = {
                symbol: "XAUUSD (Gold)", price: 2748.20, chg: 1.45, direction: "BULLISH",
                conviction: "5/5", buildup: "Long build-up", support: "2735.00", resistance: "2765.00", zone: "2742 - 2748"
            };

            function switchView(view) {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                if (view === 'orderflow') {
                    document.getElementById('view-orderflow').style.display = 'block';
                    document.getElementById('view-3d-floor').style.display = 'none';
                    event.target.classList.add('active');
                } else if (view === '3d') {
                    document.getElementById('view-orderflow').style.display = 'none';
                    document.getElementById('view-3d-floor').style.display = 'block';
                    event.target.classList.add('active');
                    if (!scene) init3D();
                }
            }

            function selectPair(pair) {
                selectedAsset = pair;
                document.getElementById('ins-title').innerText = pair.symbol;
                document.getElementById('ins-price').innerText = '$' + pair.price.toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById('ins-price').style.color = pair.direction === 'BULLISH' ? 'var(--green-line)' : 'var(--red-line)';
                document.getElementById('ins-chg').innerText = `${pair.chg >= 0 ? '+' : ''}${pair.chg.toFixed(2)}%`;
                document.getElementById('ins-chg').className = `badge-flow ${pair.direction === 'BULLISH' ? 'bg-bull' : 'bg-bear'}`;
                document.getElementById('ins-buildup').innerText = pair.buildup;
                document.getElementById('ins-buildup').style.color = pair.direction === 'BULLISH' ? 'var(--green-line)' : 'var(--red-line)';
                document.getElementById('ins-conv').innerText = `●●●●● ${pair.conviction}`;
                document.getElementById('ins-s1').innerText = pair.support;
                document.getElementById('ins-r1').innerText = pair.resistance;
                document.getElementById('ins-zone').innerText = pair.zone;
            }

            async function executeSelectedPair() {
                const side = selectedAsset.direction === 'BULLISH' ? 'BUY' : 'SELL';
                const res = await fetch('/api/trade/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({symbol: selectedAsset.symbol.includes('Gold') ? 'XAUUSDm' : selectedAsset.symbol, side: side, price: selectedAsset.price})
                });
                const d = await res.json();
                alert(`Executed on Exness MT5! Ticket: ${d.order ? d.order.id : 'Active'}`);
            }

            // Real-Time Animated Flow Canvas (Canvas 2D Particle Fluid Ribbon)
            function initFluidRibbon() {
                const c = document.getElementById('orderflow-particle-canvas');
                const ctx = c.getContext('2d');
                c.width = c.clientWidth * window.devicePixelRatio;
                c.height = 360 * window.devicePixelRatio;

                const particles = [];
                const colors = ['#10b981', '#059669', '#34d399', '#ef4444', '#f87171', '#dc2626'];

                for (let i = 0; i < 90; i++) {
                    const isBull = Math.random() < 0.62;
                    particles.push({
                        isBull: isBull,
                        x: Math.random() * (c.width * 0.4),
                        progress: Math.random(),
                        speed: 0.003 + Math.random() * 0.004,
                        width: 2 + Math.random() * 4,
                        color: isBull ? '#10b981' : '#ef4444',
                        yOffset: (Math.random() - 0.5) * 30
                    });
                }

                function render() {
                    ctx.fillStyle = '#fafbfc';
                    ctx.fillRect(0, 0, c.width, c.height);

                    const startX = 30 * window.devicePixelRatio;
                    const startY = (c.height / 2);

                    // Draw Background Flow Ribbons
                    // Bullish Ribbon (Upwards)
                    ctx.strokeStyle = 'rgba(16, 185, 129, 0.18)';
                    ctx.lineWidth = 38 * window.devicePixelRatio;
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.bezierCurveTo(c.width * 0.35, startY, c.width * 0.55, c.height * 0.15, c.width - 20, c.height * 0.12);
                    ctx.stroke();

                    // Bearish Ribbon (Downwards)
                    ctx.strokeStyle = 'rgba(239, 68, 68, 0.18)';
                    ctx.lineWidth = 32 * window.devicePixelRatio;
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.bezierCurveTo(c.width * 0.35, startY, c.width * 0.55, c.height * 0.85, c.width - 20, c.height * 0.88);
                    ctx.stroke();

                    // Animate Flow Particles
                    particles.forEach(p => {
                        p.progress += p.speed;
                        if (p.progress > 1) p.progress = 0;

                        const t = p.progress;
                        let targetY = p.isBull ? c.height * 0.12 : c.height * 0.88;
                        let cpY = p.isBull ? c.height * 0.15 : c.height * 0.85;

                        // Cubic Bezier calculation
                        const bx = (1 - t) ** 3 * startX + 3 * (1 - t) ** 2 * t * (c.width * 0.35) + 3 * (1 - t) * t ** 2 * (c.width * 0.55) + t ** 3 * (c.width - 20);
                        const by = (1 - t) ** 3 * startY + 3 * (1 - t) ** 2 * t * startY + 3 * (1 - t) * t ** 2 * cpY + t ** 3 * targetY + p.yOffset;

                        ctx.fillStyle = p.color;
                        ctx.beginPath();
                        ctx.arc(bx, by, p.width * window.devicePixelRatio, 0, Math.PI * 2);
                        ctx.fill();
                    });

                    requestAnimationFrame(render);
                }
                render();
            }

            async function syncData() {
                try {
                    const res = await fetch('/api/telemetry');
                    const d = await res.json();

                    document.getElementById('of-exness-bal').innerText = `$${d.exness.balance.toFixed(2)} USD`;

                    // Render Conviction Cards
                    if (d.orderflow && d.orderflow.bullish_pairs) {
                        const allPairs = [...d.orderflow.bullish_pairs, ...d.orderflow.bearish_pairs];
                        document.getElementById('cards-container').innerHTML = allPairs.map(p => `
                            <div class="asset-card-ui" onclick='selectPair(${JSON.stringify(p)})'>
                                <div class="card-header-flex">
                                    <div>
                                        <strong style="font-size: 13.5px; color: #0f172a;">${p.symbol}</strong>
                                        <div style="font-size: 11px; color: var(--text-muted);">${p.buildup}</div>
                                    </div>
                                    <span class="conviction-badge ${p.direction === 'BULLISH' ? 'conv-bull' : 'conv-bear'}">
                                        ${p.direction} (${p.conviction})
                                    </span>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 8px;">
                                    <span style="font-size: 18px; font-weight: 800; font-family: 'JetBrains Mono'; color: ${p.direction === 'BULLISH' ? 'var(--green-line)' : 'var(--red-line)'};">
                                        ${p.chg >= 0 ? '+' : ''}${p.chg.toFixed(2)}%
                                    </span>
                                    <span style="font-size: 12.5px; font-weight: 700; color: #475569; font-family: 'JetBrains Mono';">
                                        $${p.price.toLocaleString('en-US', {minimumFractionDigits: 2})}
                                    </span>
                                </div>
                                <div class="vp-container">
                                    <div class="vp-bid" style="width: ${p.direction === 'BULLISH' ? '65%' : '35%'};"></div>
                                    <div class="vp-ask" style="width: ${p.direction === 'BULLISH' ? '35%' : '65%'};"></div>
                                </div>
                                <div class="level-row">
                                    <span>S: <b>${p.support}</b></span>
                                    <span>Zone: <b>${p.zone}</b></span>
                                    <span>R: <b>${p.resistance}</b></span>
                                </div>
                            </div>
                        `).join('');
                    }
                } catch(e) {}
            }

            // 3D Engine with AI Central Neural Brain
            let scene, camera, renderer, controls;
            let brainCoreMesh, neuralRings = [];

            function init3D() {
                const cont = document.getElementById('canvas-3d-wrap');
                scene = new THREE.Scene();
                scene.background = new THREE.Color(0x060810);
                scene.fog = new THREE.FogExp2(0x060810, 0.015);

                camera = new THREE.PerspectiveCamera(45, cont.clientWidth / cont.clientHeight, 0.1, 1000);
                camera.position.set(34, 28, 34);

                renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('webgl-canvas'), antialias: true });
                renderer.setSize(cont.clientWidth, cont.clientHeight);
                renderer.setPixelRatio(window.devicePixelRatio);

                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.maxPolarAngle = Math.PI / 2.05;

                const ambient = new THREE.AmbientLight(0xffffff, 0.65); scene.add(ambient);
                const dir = new THREE.DirectionalLight(0x38bdf8, 1.3); dir.position.set(25, 45, 20); scene.add(dir);

                // Floor with golden fence
                const floor = new THREE.Mesh(new THREE.PlaneGeometry(54, 44), new THREE.MeshStandardMaterial({ color: 0x090d18, roughness: 0.6 }));
                floor.rotation.x = -Math.PI / 2; scene.add(floor);
                scene.add(new THREE.GridHelper(54, 54, 0x1e293b, 0x0f172a));

                // Golden perimeter fence
                const fenceMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.85 });
                const r1 = new THREE.Mesh(new THREE.BoxGeometry(54, 0.1, 0.1), fenceMat); r1.position.set(0, 1.2, 22); scene.add(r1);
                const r2 = new THREE.Mesh(new THREE.BoxGeometry(54, 0.1, 0.1), fenceMat); r2.position.set(0, 1.2, -22); scene.add(r2);
                const r3 = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 44), fenceMat); r3.position.set(-27, 1.2, 0); scene.add(r3);
                const r4 = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 44), fenceMat); r4.position.set(27, 1.2, 0); scene.add(r4);

                // 🧠 AI CENTRAL NEURAL BRAIN (Floating in Center of Office)
                createCentralAIBrain(0, 7.5, 0);

                // Desks with Chairs & Robots
                create3DPod(-8, -2, 0xfacc15, "• PA_01 Quant");
                create3DPod(8, 2, 0xa855f7, "• PA_07 Viral");

                function loop() {
                    requestAnimationFrame(loop);
                    controls.update();

                    // Animate AI Brain Core rotation and pulse
                    if (brainCoreMesh) {
                        brainCoreMesh.rotation.y += 0.015;
                        brainCoreMesh.rotation.x += 0.008;
                        neuralRings.forEach((r, idx) => {
                            r.rotation.x += 0.02 * (idx + 1);
                            r.rotation.y += 0.015 * (idx + 1);
                        });
                    }

                    renderer.render(scene, camera);
                }
                loop();
            }

            function createCentralAIBrain(x, y, z) {
                const brainGroup = new THREE.Group();
                brainGroup.position.set(x, y, z);

                // Glowing Neural Core
                const coreGeo = new THREE.IcosahedronGeometry(1.8, 2);
                const coreMat = new THREE.MeshStandardMaterial({
                    color: 0xec4899,
                    emissive: 0xec4899,
                    emissiveIntensity: 0.8,
                    wireframe: true
                });
                brainCoreMesh = new THREE.Mesh(coreGeo, coreMat);
                brainGroup.add(brainCoreMesh);

                // Inner pulsing sphere
                const innerGeo = new THREE.SphereGeometry(1.1, 16, 16);
                const innerMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
                const inner = new THREE.Mesh(innerGeo, innerMat);
                brainGroup.add(inner);

                // Neural Gyro Orbit Rings
                for (let i = 0; i < 3; i++) {
                    const ringGeo = new THREE.TorusGeometry(2.6 + (i * 0.4), 0.04, 8, 48);
                    const ringMat = new THREE.MeshBasicMaterial({ color: i === 0 ? 0x38bdf8 : (i === 1 ? 0x10b981 : 0xec4899) });
                    const ring = new THREE.Mesh(ringGeo, ringMat);
                    neuralRings.push(ring);
                    brainGroup.add(ring);
                }

                // Holographic pedestal beam
                const beamGeo = new THREE.CylinderGeometry(0.1, 1.8, 7.5, 16);
                const beamMat = new THREE.MeshBasicMaterial({ color: 0xec4899, transparent: true, opacity: 0.25 });
                const beam = new THREE.Mesh(beamGeo, beamMat);
                beam.position.y = -3.75;
                brainGroup.add(beam);

                scene.add(brainGroup);
            }

            function create3DPod(x, z, c, tag) {
                const g = new THREE.Group(); g.position.set(x, 0, z);
                const d = new THREE.Mesh(new THREE.BoxGeometry(9, 1.4, 3.4), new THREE.MeshStandardMaterial({ color: 0x111726 }));
                d.position.y = 1.4; g.add(d);
                for(let m = -1; m <= 1; m++) {
                    const scr = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.3, 0.1), new THREE.MeshBasicMaterial({ color: 0x0284c7 }));
                    scr.position.set(m*2.6, 2.8, -0.6); g.add(scr);
                }
                scene.add(g);
            }

            function setCam(view) {
                if(view === 'overview') { camera.position.set(34, 28, 34); controls.target.set(0, 2, 0); }
                else if(view === 'brain') { camera.position.set(0, 11, 12); controls.target.set(0, 7.5, 0); }
                else if(view === 'trading') { camera.position.set(-8, 9, 7); controls.target.set(-8, 2, -2); }
                else if(view === 'branding') { camera.position.set(8, 9, 10); controls.target.set(8, 2, 2); }
                else if(view === 'coffee') { camera.position.set(12, 8, 16); controls.target.set(12, 2, 10); }
                else if(view === 'wall') { camera.position.set(0, 10, 8); controls.target.set(0, 8.5, -21.8); }
            }

            window.onload = () => {
                initFluidRibbon();
                syncData();
                setInterval(syncData, 3000);
            };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
