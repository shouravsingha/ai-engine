import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.orchestrator import MasterOrchestrator

app = FastAPI(title="Production Institutional AI Trading Floor & Media Office")
orchestrator = MasterOrchestrator()

@app.on_event("startup")
def startup_event():
    orchestrator.start_background_loop()

@app.get("/api/telemetry")
def get_telemetry():
    return JSONResponse({
        "account": orchestrator.account.get_summary(),
        "exness": orchestrator.exness.get_status(),
        "gold_analysis": orchestrator.gold_analysis,
        "btc_analysis": orchestrator.btc_analysis,
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
    
    # Process directive with agent intelligence
    if "gold" in task_text.lower() or "xau" in task_text.lower():
        orchestrator.send_agent_message("Alex", "Chief Quant", "Prioritizing Gold (XAUUSD) 15m/1H/4H structure scan...")
        orchestrator.send_agent_message("David", "Fibonacci Specialist", "Gold Golden Pocket OTE recalculated for next entry.")
        orchestrator.telegram.send_message(f"🥇 <b>DIRECTIVE ACKNOWLEDGED:</b> {task_text}\nGold SMC Desk prioritized.")
    elif "coffee" in task_text.lower():
        orchestrator.send_agent_message("Mia", "Viral Copywriter", "Heading to the coffee bar! ☕")
        orchestrator.send_agent_message("Leo", "Execution Trader", "Two minutes at the coffee bar. Trailing stops active.")
    elif "broadcast" in task_text.lower() or "social" in task_text.lower() or "news" in task_text.lower():
        post = orchestrator.branding.generate_firm_content("BULLISH", "$2,745 (Gold)")
        orchestrator.webhooks.broadcast_branding(post["headline"], post["content"])
        orchestrator.telegram.send_branding_alert(post["headline"], post["content"])
        orchestrator.send_agent_message("Sophia", "Brand Director", f"Dispatched breaking broadcast to all social webhooks & Telegram!")
    else:
        orchestrator.send_agent_message("Alex", "Chief Quant", f"Directive received: '{task_text}'. Team executing now.")

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
    orchestrator.send_agent_message("Sophia", "Brand Director", "Multi-platform social webhooks updated & armed.")
    return {"status": "success", "webhooks": orchestrator.webhooks.webhooks}

@app.post("/api/broadcast/test")
def test_broadcast():
    post = orchestrator.branding.generate_firm_content("BULLISH", "$2,745.50")
    orchestrator.webhooks.broadcast_branding(post["headline"], post["content"])
    orchestrator.telegram.send_branding_alert(post["headline"], post["content"])
    return {"status": "success", "post": post}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TradingAI · 3D Virtual Quant Desk & Media Office</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <!-- Three.js + OrbitControls -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            :root {
                --bg: #060810;
                --panel: rgba(11, 15, 27, 0.94);
                --border: #182236;
                --accent-blue: #38bdf8;
                --accent-green: #10b981;
                --accent-gold: #f59e0b;
                --accent-purple: #a855f7;
                --accent-red: #f43f5e;
                --text: #f8fafc;
                --muted: #8292a8;
            }
            * { box-sizing: border-box; }
            body, html {
                margin: 0; padding: 0; width: 100%; height: 100%;
                overflow: hidden; background: var(--bg); color: var(--text);
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            #app-root { display: grid; grid-template-rows: 52px 1fr; width: 100vw; height: 100vh; }
            
            /* Top App Bar */
            .top-bar {
                background: #080c16; border-bottom: 1px solid var(--border);
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 20px; z-index: 50;
            }
            .brand-badge { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 15px; }
            .pill { padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; }
            .pill-gold { background: rgba(245, 158, 11, 0.15); color: var(--accent-gold); border: 1px solid rgba(245, 158, 11, 0.3); }
            .pill-blue { background: rgba(56, 189, 248, 0.15); color: var(--accent-blue); }
            .pill-green { background: rgba(16, 185, 129, 0.15); color: var(--accent-green); }

            /* Three Columns */
            .main-content {
                display: grid; grid-template-columns: 310px 1fr 340px;
                height: calc(100vh - 52px); position: relative;
            }
            .sidebar {
                background: var(--panel); backdrop-filter: blur(12px);
                padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;
                z-index: 20;
            }
            .sidebar-left { border-right: 1px solid var(--border); }
            .sidebar-right { border-left: 1px solid var(--border); }

            /* Market Switcher Header */
            .asset-toggle {
                display: flex; background: #070a14; border: 1px solid var(--border);
                border-radius: 8px; padding: 3px; gap: 4px;
            }
            .asset-btn {
                flex: 1; background: transparent; border: none; color: var(--muted);
                padding: 8px; border-radius: 6px; font-weight: 700; font-size: 11.5px;
                cursor: pointer; transition: all 0.2s;
            }
            .asset-btn.active { background: #131b2c; color: #fff; border: 1px solid var(--border); }
            .asset-btn.active.gold-btn { color: var(--accent-gold); }

            /* Metric Cards */
            .card {
                background: #090e1a; border: 1px solid var(--border);
                border-radius: 10px; padding: 12px 14px;
            }
            .card-title { font-size: 10.5px; color: var(--muted); text-transform: uppercase; font-weight: 700; }
            .card-val { font-size: 20px; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }

            /* Buttons */
            .btn {
                width: 100%; padding: 8px 12px; border-radius: 6px; border: none;
                font-weight: 700; font-size: 12px; cursor: pointer; transition: opacity 0.2s;
            }
            .btn-blue { background: var(--accent-blue); color: #000; }
            .btn-gold { background: var(--accent-gold); color: #000; }
            .btn-secondary { background: #131a29; border: 1px solid var(--border); color: #cbd5e1; }
            .btn-secondary:hover { background: #1c273c; color: #fff; }

            /* 3D Viewport */
            #viewport-3d { position: relative; width: 100%; height: 100%; overflow: hidden; }
            #webgl-canvas { width: 100%; height: 100%; display: block; }
            
            .hud-overlay {
                position: absolute; top: 16px; left: 16px; right: 16px;
                display: flex; justify-content: space-between; pointer-events: none; z-index: 10;
            }
            .hud-card {
                background: rgba(9, 13, 23, 0.9); backdrop-filter: blur(10px);
                border: 1px solid var(--border); border-radius: 20px;
                padding: 6px 16px; font-size: 12px; font-weight: 700; pointer-events: auto;
                display: flex; align-items: center; gap: 8px;
            }

            .dock {
                position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                background: rgba(9, 13, 23, 0.9); backdrop-filter: blur(14px);
                border: 1px solid var(--border); border-radius: 30px;
                padding: 5px 10px; display: flex; gap: 6px; z-index: 10;
            }
            .dock-btn {
                background: transparent; border: none; color: var(--muted);
                padding: 6px 14px; border-radius: 20px; font-size: 11px; font-weight: 700;
                cursor: pointer;
            }
            .dock-btn.active, .dock-btn:hover { background: var(--accent-blue); color: #000; }

            /* Right Chat */
            .chat-list {
                flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; margin-top: 10px;
            }
            .chat-bubble {
                background: #080c16; border: 1px solid var(--border); border-radius: 8px;
                padding: 9px 11px; font-size: 12px; line-height: 1.45; animation: fadeIn 0.2s ease;
            }
            .chat-meta { display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); margin-bottom: 3px; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

            /* Modal */
            .modal-bg {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0,0,0,0.75); backdrop-filter: blur(8px);
                display: none; align-items: center; justify-content: center; z-index: 1000;
            }
            .modal-card {
                background: #0e1320; border: 1px solid var(--border); border-radius: 12px;
                padding: 22px; width: 440px; box-shadow: 0 20px 50px rgba(0,0,0,0.8);
            }
            .input-group { margin-bottom: 12px; }
            .input-group label { display: block; font-size: 11px; font-weight: 700; color: var(--muted); margin-bottom: 4px; }
            .input-group input {
                width: 100%; padding: 9px; border-radius: 6px; border: 1px solid var(--border);
                background: #07090f; color: #fff; font-family: inherit; font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div id="app-root">
            <!-- TOP APP BAR -->
            <header class="top-bar">
                <div class="brand-badge">
                    <span>🏛️ TradingAI Production Desk</span>
                    <span class="pill pill-gold">🥇 GOLD (XAUUSD) & BTC ACTIVE</span>
                </div>
                <div style="display: flex; align-items: center; gap: 14px;">
                    <span class="pill pill-green" id="telegram-pill">● @SingAiTradebot SENTINEL LIVE</span>
                    <span class="pill pill-blue">Exness MT5: #434353249</span>
                    <button class="btn btn-secondary" onclick="openWebhookModal()" style="width: auto; padding: 5px 12px; font-size: 11px;">🌐 Webhooks</button>
                </div>
            </header>

            <main class="main-content">
                <!-- LEFT SIDEBAR -->
                <aside class="sidebar sidebar-left">
                    <!-- Asset Toggle -->
                    <div class="asset-toggle">
                        <button id="btn-asset-gold" class="asset-btn active gold-btn" onclick="toggleActiveAsset('gold')">🥇 XAUUSD (Gold)</button>
                        <button id="btn-asset-btc" class="asset-btn" onclick="toggleActiveAsset('btc')">⚡ BTC/USDT</button>
                    </div>

                    <!-- Live Selected Asset Card -->
                    <div class="card" style="border-color: rgba(245,158,11,0.4);">
                        <div style="display: flex; justify-content: space-between;">
                            <span class="card-title" id="asset-label">🥇 XAUUSD SPOT</span>
                            <span id="asset-chg" style="color: var(--accent-green); font-size: 11px; font-weight: 700;">+0.85%</span>
                        </div>
                        <div id="asset-price" class="card-val" style="color: var(--accent-gold); font-size: 24px;">$2,745.50</div>
                        <div style="font-size: 11.5px; color: var(--muted); margin-top: 4px;">
                            SMC Trend: <strong id="asset-trend" style="color: var(--accent-green);">BULLISH (4H)</strong><br>
                            Zone: <strong id="asset-zone" style="color: var(--accent-gold);">DISCOUNT (0.618 OTE)</strong>
                        </div>
                    </div>

                    <!-- Exness Account Banner -->
                    <div class="card">
                        <div class="card-title">Exness MT5 Real-Time Equity</div>
                        <div id="exness-balance" class="card-val" style="color: var(--accent-green);">$20.21 USD</div>
                        <small style="color: var(--muted); font-size: 11px;">Server: Exness-MT5Trial7 · 1:2000 Hedging</small>
                    </div>

                    <!-- Directives -->
                    <div class="card">
                        <div class="card-title">Directive Command Center</div>
                        <input type="text" id="task-text" class="input-group" style="width:100%; padding:8px; border-radius:6px; border:1px solid #243048; background:#070a12; color:#fff; font-size:12px; margin-top:6px; margin-bottom:8px;" placeholder="e.g. Scan Gold 4H OTE entry...">
                        <button class="btn btn-blue" onclick="dispatchDirective()">▶ SEND DIRECTIVE</button>
                        <button class="btn btn-secondary" onclick="testSocialBroadcast()" style="margin-top:6px;">📢 Trigger Social & Telegram Broadcast</button>
                    </div>

                    <!-- Agent Activity Roster -->
                    <div>
                        <div class="card-title" style="margin-bottom: 6px;">Workforce Status (7/7)</div>
                        <div id="roster-list"></div>
                    </div>
                </aside>

                <!-- CENTER 3D FLOOR -->
                <div id="viewport-3d">
                    <div class="hud-overlay">
                        <div class="hud-card">
                            <span style="color: var(--muted);">EXNESS:</span>
                            <span style="color: var(--accent-green);" id="hud-exness">$20.21 USD</span>
                        </div>
                        <div class="hud-card">
                            <span style="color: var(--muted);">PRIMARY FOCUS:</span>
                            <span style="color: var(--accent-gold);" id="hud-primary">🥇 GOLD (XAUUSDm) SMC</span>
                        </div>
                    </div>

                    <canvas id="webgl-canvas"></canvas>

                    <div class="dock">
                        <button class="dock-btn active" onclick="setCam('overview')">Overview</button>
                        <button class="dock-btn" onclick="setCam('trading')">Quant Desk</button>
                        <button class="dock-btn" onclick="setCam('branding')">Media Studio</button>
                        <button class="dock-btn" onclick="setCam('manager')">Manager Office</button>
                        <button class="dock-btn" onclick="setCam('coffee')">Coffee Bar</button>
                        <button class="dock-btn" onclick="setCam('wall')">LED Wall</button>
                    </div>
                </div>

                <!-- RIGHT SIDEBAR: INTER-COM & LIVE ALERTS -->
                <aside class="sidebar sidebar-right">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 8px;">
                        <div>
                            <div style="font-size: 12px; font-weight: 800;">AGENT INTER-COM</div>
                            <small style="color: var(--muted); font-size: 10.5px;">Live Telegram & Desk Sync</small>
                        </div>
                        <span class="pill pill-green" style="font-size: 9.5px;">LIVE</span>
                    </div>

                    <div class="chat-list" id="intercom-stream"></div>

                    <!-- Latest Social Dispatch -->
                    <div class="card" style="margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span class="pill pill-gold" style="font-size: 9px;">AUTO WEBHOOK DISPATCH</span>
                            <small id="dispatch-time" style="color: var(--muted); font-size: 10px;">Synced</small>
                        </div>
                        <div id="dispatch-headline" style="font-size: 11.5px; font-weight: 700; color: #fff;">Gold (XAUUSD) SMC Breakdown Queued</div>
                    </div>
                </aside>
            </main>
        </div>

        <!-- WEBHOOK CONFIG MODAL -->
        <div id="webhook-modal" class="modal-bg">
            <div class="modal-card">
                <h3 style="margin-top:0; color:#fff;">🌐 Multi-Platform Social Webhooks</h3>
                <p style="font-size:12px; color:var(--muted); margin-bottom:14px;">Incoming breaking news and Gold/BTC setups auto-broadcast to these endpoints:</p>
                <div class="input-group">
                    <label>Discord Webhook URL</label>
                    <input type="text" id="wh-discord" placeholder="https://discord.com/api/webhooks/...">
                </div>
                <div class="input-group">
                    <label>Slack Webhook URL</label>
                    <input type="text" id="wh-slack" placeholder="https://hooks.slack.com/services/...">
                </div>
                <div class="input-group">
                    <label>Make / Zapier / Custom Webhook</label>
                    <input type="text" id="wh-generic" placeholder="https://hook.eu1.make.com/...">
                </div>
                <div style="display:flex; gap:10px; margin-top:16px;">
                    <button class="btn btn-blue" onclick="saveWebhooks()">Save & Arm Webhooks</button>
                    <button class="btn btn-secondary" onclick="closeWebhookModal()">Cancel</button>
                </div>
            </div>
        </div>

        <!-- THREE.JS HIGH FIDELITY SCRIPT -->
        <script>
            let scene, camera, renderer, controls;
            let ledCanvas, ledTexture;
            let activeAsset = 'gold';
            let liveExnessBal = 20.21, goldPrice = "$2,745.50", btcPrice = "$65,000.00";

            function init3D() {
                const container = document.getElementById('viewport-3d');
                const w = container.clientWidth;
                const h = container.clientHeight;

                scene = new THREE.Scene();
                scene.background = new THREE.Color(0x060810);
                scene.fog = new THREE.FogExp2(0x060810, 0.015);

                camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
                camera.position.set(32, 26, 32);

                renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('webgl-canvas'), antialias: true });
                renderer.setSize(w, h);
                renderer.setPixelRatio(window.devicePixelRatio);
                renderer.shadowMap.enabled = true;

                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.maxPolarAngle = Math.PI / 2.05;
                controls.target.set(0, 2, 0);

                const ambient = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambient);

                const dir = new THREE.DirectionalLight(0x38bdf8, 1.2);
                dir.position.set(25, 40, 20);
                scene.add(dir);

                // Floor & Golden Perimeter Fence (Video 2)
                const floor = new THREE.Mesh(new THREE.PlaneGeometry(54, 44), new THREE.MeshStandardMaterial({ color: 0x090d18, roughness: 0.6 }));
                floor.rotation.x = -Math.PI / 2;
                scene.add(floor);
                scene.add(new THREE.GridHelper(54, 54, 0x1e293b, 0x0f172a));

                const fenceMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.85 });
                const r1 = new THREE.Mesh(new THREE.BoxGeometry(54, 0.1, 0.1), fenceMat); r1.position.set(0, 1.2, 22); scene.add(r1);
                const r2 = new THREE.Mesh(new THREE.BoxGeometry(54, 0.1, 0.1), fenceMat); r2.position.set(0, 1.2, -22); scene.add(r2);
                const r3 = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 44), fenceMat); r3.position.set(-27, 1.2, 0); scene.add(r3);
                const r4 = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 44), fenceMat); r4.position.set(27, 1.2, 0); scene.add(r4);

                // LED Wall
                createLEDWall();

                // Office Areas
                createCubicles(-8, -2, 0x38bdf8);
                createMediaStudio(8, 2);
                createManagerOffice(-14, 10);
                createCoffeeLounge(12, 10);
                createServerRacks(-18, -10);

                window.addEventListener('resize', () => {
                    const cont = document.getElementById('viewport-3d');
                    camera.aspect = cont.clientWidth / cont.clientHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(cont.clientWidth, cont.clientHeight);
                });

                function loop() {
                    requestAnimationFrame(loop);
                    controls.update();
                    renderer.render(scene, camera);
                }
                loop();
            }

            function createLEDWall() {
                ledCanvas = document.createElement('canvas');
                ledCanvas.width = 1024; ledCanvas.height = 512;
                updateLEDCanvas();

                ledTexture = new THREE.CanvasTexture(ledCanvas);
                const wall = new THREE.Mesh(new THREE.PlaneGeometry(28, 12), new THREE.MeshBasicMaterial({ map: ledTexture }));
                wall.position.set(0, 8.5, -21.8);
                scene.add(wall);
            }

            function updateLEDCanvas() {
                const ctx = ledCanvas.getContext('2d');
                ctx.fillStyle = '#03050a'; ctx.fillRect(0, 0, 1024, 512);

                ctx.fillStyle = '#38bdf8'; ctx.font = 'bold 34px "Plus Jakarta Sans"';
                ctx.fillText('TRADINGAI · EXNESS MT5 QUANT FLOOR', 40, 60);

                ctx.fillStyle = '#94a3b8'; ctx.font = '20px "JetBrains Mono"';
                ctx.fillText('ACCOUNT #434353249 · Exness-MT5Trial7 · @SingAiTradebot', 40, 95);

                ctx.fillStyle = '#10b981'; ctx.font = 'bold 68px "JetBrains Mono"';
                ctx.fillText(`US$ ${liveExnessBal.toLocaleString('en-US', {minimumFractionDigits: 2})}`, 40, 175);

                // Gold & BTC Badges
                ctx.fillStyle = '#f59e0b'; ctx.font = 'bold 22px "JetBrains Mono"';
                ctx.fillText(`🥇 GOLD: ${goldPrice} (0.618 OTE)`, 40, 220);
                ctx.fillStyle = '#38bdf8';
                ctx.fillText(`⚡ BTC: ${btcPrice}`, 520, 220);

                // Chart Line
                ctx.strokeStyle = '#10b981'; ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.moveTo(40, 440); ctx.lineTo(180, 410); ctx.lineTo(340, 430);
                ctx.lineTo(500, 330); ctx.lineTo(680, 360); ctx.lineTo(840, 250); ctx.lineTo(980, 230);
                ctx.stroke();

                ctx.fillStyle = 'rgba(16, 185, 129, 0.12)';
                ctx.lineTo(980, 480); ctx.lineTo(40, 480); ctx.closePath(); ctx.fill();

                if (ledTexture) ledTexture.needsUpdate = true;
            }

            function createCubicles(x, z, color) {
                const grp = new THREE.Group(); grp.position.set(x, 0, z);
                for (let r = 0; r < 2; r++) {
                    const desk = new THREE.Mesh(new THREE.BoxGeometry(10, 1.4, 3.4), new THREE.MeshStandardMaterial({ color: 0x111726 }));
                    desk.position.set(0, 1.4, r * 5); grp.add(desk);
                    for (let m = -1; m <= 1; m++) {
                        const scr = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.3, 0.1), new THREE.MeshBasicMaterial({ color: 0x0284c7 }));
                        scr.position.set(m * 2.8, 2.8, (r * 5) - 0.6); grp.add(scr);
                        createRobot(grp, m * 2.8, 0.8, (r * 5) + 1.2, color);
                    }
                }
                scene.add(grp);
            }

            function createMediaStudio(x, z) {
                const grp = new THREE.Group(); grp.position.set(x, 0, z);
                const desk = new THREE.Mesh(new THREE.BoxGeometry(9, 1.4, 3.4), new THREE.MeshStandardMaterial({ color: 0x1a1226 }));
                desk.position.set(0, 1.4, 0); grp.add(desk);
                for (let m = -1; m <= 1; m++) {
                    const scr = new THREE.Mesh(new THREE.BoxGeometry(2.2, 1.3, 0.1), new THREE.MeshBasicMaterial({ color: 0xa855f7 }));
                    scr.position.set(m * 2.6, 2.8, -0.6); grp.add(scr);
                    createRobot(grp, m * 2.6, 0.8, 1.2, 0xa855f7);
                }
                scene.add(grp);
            }

            function createManagerOffice(x, z) {
                const grp = new THREE.Group(); grp.position.set(x, 0, z);
                const desk = new THREE.Mesh(new THREE.BoxGeometry(6, 1.5, 3.2), new THREE.MeshStandardMaterial({ color: 0x3b1c11 }));
                desk.position.y = 1.4; grp.add(desk);
                const trophy = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.15, 0.7), new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8 }));
                trophy.position.set(-1.6, 2.5, 0.4); grp.add(trophy);
                scene.add(grp);
            }

            function createCoffeeLounge(x, z) {
                const grp = new THREE.Group(); grp.position.set(x, 0, z);
                const bar = new THREE.Mesh(new THREE.BoxGeometry(7, 1.6, 2.2), new THREE.MeshStandardMaterial({ color: 0x18181b }));
                bar.position.y = 1.4; grp.add(bar);
                const machine = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.1, 0.9), new THREE.MeshStandardMaterial({ color: 0xef4444 }));
                machine.position.set(-1.8, 2.7, 0); grp.add(machine);
                scene.add(grp);
            }

            function createServerRacks(x, z) {
                for (let i = 0; i < 3; i++) {
                    const r = new THREE.Mesh(new THREE.BoxGeometry(2.4, 7.5, 2.2), new THREE.MeshStandardMaterial({ color: 0x090d16 }));
                    r.position.set(x + (i * 3), 3.75, z); scene.add(r);
                }
            }

            function createRobot(p, x, y, z, c) {
                const bot = new THREE.Group(); bot.position.set(x, y, z);
                const b = new THREE.Mesh(new THREE.BoxGeometry(0.85, 1.1, 0.65), new THREE.MeshStandardMaterial({ color: 0x1e293b }));
                b.position.y = 1.1; bot.add(b);
                const h = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.6, 0.6), new THREE.MeshStandardMaterial({ color: 0x0f172a }));
                h.position.y = 2.0; bot.add(h);
                const v = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.16, 0.05), new THREE.MeshBasicMaterial({ color: c }));
                v.position.set(0, 2.0, 0.31); bot.add(v);
                p.add(bot);
            }

            function setCam(view) {
                document.querySelectorAll('.dock-btn').forEach(b => b.classList.remove('active'));
                if (event && event.target) event.target.classList.add('active');
                if (view === 'overview') { camera.position.set(32, 26, 32); controls.target.set(0, 2, 0); }
                else if (view === 'trading') { camera.position.set(-8, 9, 7); controls.target.set(-8, 2, -2); }
                else if (view === 'branding') { camera.position.set(8, 9, 10); controls.target.set(8, 2, 2); }
                else if (view === 'manager') { camera.position.set(-14, 8, 17); controls.target.set(-14, 2, 10); }
                else if (view === 'coffee') { camera.position.set(12, 8, 16); controls.target.set(12, 2, 10); }
                else if (view === 'wall') { camera.position.set(0, 10, 8); controls.target.set(0, 8.5, -21.8); }
            }

            // Asset Toggle (Gold / BTC)
            function toggleActiveAsset(asset) {
                activeAsset = asset;
                document.getElementById('btn-asset-gold').classList.toggle('active', asset === 'gold');
                document.getElementById('btn-asset-btc').classList.toggle('active', asset === 'btc');
                syncUI();
            }

            async function dispatchDirective() {
                const inp = document.getElementById('task-text');
                const t = inp.value.trim(); if (!t) return;
                inp.value = '';
                await fetch('/api/task', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({task: t})});
                syncData();
            }

            async function testSocialBroadcast() {
                await fetch('/api/broadcast/test', {method: 'POST'});
                syncData();
            }

            function openWebhookModal() { document.getElementById('webhook-modal').style.display = 'flex'; }
            function closeWebhookModal() { document.getElementById('webhook-modal').style.display = 'none'; }

            async function saveWebhooks() {
                const d = document.getElementById('wh-discord').value;
                const s = document.getElementById('wh-slack').value;
                const g = document.getElementById('wh-generic').value;
                await fetch('/api/webhooks/save', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({discord: d, slack: s, generic_social: g})
                });
                closeWebhookModal();
            }

            let cacheData = null;
            function syncUI() {
                if (!cacheData) return;
                const d = cacheData;
                liveExnessBal = d.exness.balance;
                document.getElementById('exness-balance').innerText = `$${liveExnessBal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;
                document.getElementById('hud-exness').innerText = `$${liveExnessBal.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;

                if (d.gold_analysis && d.gold_analysis.current_price) {
                    goldPrice = `$${d.gold_analysis.current_price.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                }
                if (d.btc_analysis && d.btc_analysis.current_price) {
                    btcPrice = `$${d.btc_analysis.current_price.toLocaleString('en-US', {minimumFractionDigits: 2})}`;
                }

                if (activeAsset === 'gold' && d.gold_analysis) {
                    document.getElementById('asset-label').innerText = '🥇 XAUUSD SPOT';
                    document.getElementById('asset-price').innerText = goldPrice;
                    document.getElementById('asset-price').style.color = 'var(--accent-gold)';
                    document.getElementById('asset-trend').innerText = `${d.gold_analysis.trend} (4H)`;
                    document.getElementById('asset-zone').innerText = d.gold_analysis.zone_status;
                } else if (d.btc_analysis) {
                    document.getElementById('asset-label').innerText = '⚡ BITCOIN (BTCUSDT)';
                    document.getElementById('asset-price').innerText = btcPrice;
                    document.getElementById('asset-price').style.color = 'var(--accent-blue)';
                    document.getElementById('asset-trend').innerText = `${d.btc_analysis.trend} (4H)`;
                    document.getElementById('asset-zone').innerText = d.btc_analysis.zone_status;
                }

                updateLEDCanvas();

                // Roster
                if (d.agents) {
                    document.getElementById('roster-list').innerHTML = d.agents.map(a => `
                        <div style="display:flex; justify-content:space-between; padding:7px 0; border-bottom:1px solid #141c2c; font-size:11.5px;">
                            <span style="color:${a.color}; font-weight:700;">${a.name} (${a.dept})</span>
                            <span style="font-size:10.5px; color:var(--muted);">${a.status}</span>
                        </div>
                    `).join('');
                }

                // Chat
                if (d.agent_messages) {
                    document.getElementById('intercom-stream').innerHTML = d.agent_messages.map(m => `
                        <div class="chat-bubble">
                            <div class="chat-meta"><span style="color:var(--accent-blue); font-weight:700;">${m.agent} (${m.role})</span><span>${m.time}</span></div>
                            <div>${m.text}</div>
                        </div>
                    `).join('');
                }
            }

            async function syncData() {
                try {
                    const res = await fetch('/api/telemetry');
                    cacheData = await res.json();
                    syncUI();
                } catch(e) {}
            }

            window.onload = () => {
                init3D();
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
