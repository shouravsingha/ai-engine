import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.orchestrator import MasterOrchestrator

app = FastAPI(title="3D Virtual AI Trading Floor & Media Office")
orchestrator = MasterOrchestrator()

@app.on_event("startup")
def startup_event():
    orchestrator.start_background_loop()

@app.get("/api/telemetry")
def get_telemetry():
    return JSONResponse({
        "account": orchestrator.account.get_summary(),
        "exness": orchestrator.exness.get_status(),
        "agents": orchestrator.agents,
        "agent_messages": orchestrator.agent_messages,
        "open_trades": orchestrator.account.open_trades,
        "trade_history": orchestrator.account.trade_history[-10:],
        "market_analysis": orchestrator.last_analysis,
        "branding_posts": orchestrator.branding.get_feed(),
        "logs": orchestrator.system_logs
    })

class TaskInput(BaseModel):
    task: str

@app.post("/api/task")
def assign_task(data: TaskInput):
    task_text = data.task.strip()
    orchestrator.send_agent_message("You (Director)", "Firm Director", f"🎯 NEW DIRECTIVE: {task_text}")
    
    # Context-aware agent responses
    if "coffee" in task_text.lower():
        orchestrator.send_agent_message("Mia", "Viral Copywriter", "Heading to the coffee bar! ☕")
        orchestrator.send_agent_message("Leo", "Execution Trader", "Grabbing a coffee, terminal running trailing stop.")
    elif "scan" in task_text.lower() or "smc" in task_text.lower():
        orchestrator.send_agent_message("Alex", "Chief Quant", "Scanning 4H/1H candles for BOS and Order Blocks...")
        orchestrator.send_agent_message("David", "Fibonacci Specialist", "Calculating 0.618-0.786 Golden Pocket OTE levels.")
    elif "exness" in task_text.lower() or "sync" in task_text.lower():
        orchestrator.exness.refresh_balance()
        orchestrator.send_agent_message("Leo", "Execution Trader", f"Exness MT5 verified: Account #{orchestrator.exness.account_id} on {orchestrator.exness.server} ($ {orchestrator.exness.balance:,.2f})")
    elif "twitter" in task_text.lower() or "brand" in task_text.lower() or "post" in task_text.lower():
        orchestrator.branding.generate_firm_content("BULLISH", "$65,000")
        orchestrator.send_agent_message("Sophia", "Brand Director", "Campaign approved. Mia is drafting the thread now.")
    else:
        orchestrator.send_agent_message("Alex", "Chief Quant", f"Directive received: '{task_text}'. Team executing now.")

    return {"status": "success", "message": "Task dispatched to team"}

class ExnessConnectInput(BaseModel):
    account_id: str
    server: Optional[str] = "Exness-MT5Trial7"
    balance: Optional[float] = 20.21

@app.post("/api/exness/connect")
def connect_exness(data: ExnessConnectInput):
    res = orchestrator.exness.connect_account(
        account_id=data.account_id,
        server=data.server,
        balance=data.balance
    )
    orchestrator.send_agent_message("Leo", "Execution Trader", f"Exness MT5 Linked: Account #{data.account_id} on {data.server} ($ {orchestrator.exness.balance:,.2f})")
    return {"status": "success", "exness": res}

@app.get("/", response_class=HTMLResponse)
def virtual_office_app():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Agent Virtual Office · 3D Quant Trading Floor</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <!-- Three.js + OrbitControls -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            :root {
                --bg: #07090f;
                --sidebar-bg: rgba(12, 16, 28, 0.94);
                --card-bg: #0d121f;
                --card-border: #1a2236;
                --accent-blue: #38bdf8;
                --accent-green: #10b981;
                --accent-gold: #f59e0b;
                --accent-purple: #a855f7;
                --accent-red: #f43f5e;
                --text-main: #f8fafc;
                --text-muted: #8292a8;
            }
            * { box-sizing: border-box; }
            body, html {
                margin: 0; padding: 0; width: 100%; height: 100%;
                overflow: hidden; background: var(--bg); color: var(--text-main);
                font-family: 'Plus Jakarta Sans', sans-serif;
            }

            /* Main Layout */
            #app-root {
                display: grid;
                grid-template-rows: 54px 1fr;
                width: 100vw; height: 100vh;
            }

            /* Top App Bar */
            .top-bar {
                background: #090d17;
                border-bottom: 1px solid var(--card-border);
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 20px; z-index: 50;
            }
            .brand-badge {
                display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 15px;
            }
            .brand-pill {
                background: rgba(56, 189, 248, 0.15); color: var(--accent-blue);
                padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700;
            }
            .top-nav { display: flex; gap: 6px; }
            .nav-link {
                background: transparent; border: none; color: var(--text-muted);
                padding: 7px 14px; border-radius: 8px; font-size: 12.5px; font-weight: 600;
                cursor: pointer; transition: all 0.2s;
            }
            .nav-link.active, .nav-link:hover {
                background: #141c2e; color: #fff;
            }
            .top-right-status {
                display: flex; align-items: center; gap: 12px; font-size: 12px;
            }
            .pulse-dot {
                width: 8px; height: 8px; border-radius: 50%; background: var(--accent-green);
                box-shadow: 0 0 10px var(--accent-green); animation: pulse 1.6s infinite;
            }
            @keyframes pulse { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }

            /* Three Column Floor Layout */
            .main-content {
                display: grid;
                grid-template-columns: 310px 1fr 340px;
                height: calc(100vh - 54px);
                position: relative;
            }

            /* Left Sidebar: Team & Tasks */
            .panel-left {
                background: var(--sidebar-bg);
                backdrop-filter: blur(12px);
                border-right: 1px solid var(--card-border);
                padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px;
                z-index: 20;
            }
            /* Right Sidebar: Agent Communication */
            .panel-right {
                background: var(--sidebar-bg);
                backdrop-filter: blur(12px);
                border-left: 1px solid var(--card-border);
                padding: 16px; overflow-y: auto; display: flex; flex-direction: column;
                z-index: 20;
            }

            /* Metric Cards */
            .metrics-grid {
                display: grid; grid-template-columns: 1fr 1fr; gap: 8px;
            }
            .metric-card {
                background: var(--card-bg); border: 1px solid var(--card-border);
                border-radius: 10px; padding: 10px 12px;
            }
            .metric-label { font-size: 10.5px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }
            .metric-val { font-size: 18px; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 4px; }

            /* Exness Connected Banner */
            .exness-banner {
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 78, 59, 0.2));
                border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 10px;
                padding: 12px; display: flex; justify-content: space-between; align-items: center;
            }

            /* Task Input Section */
            .task-box {
                background: var(--card-bg); border: 1px solid var(--card-border);
                border-radius: 10px; padding: 12px;
            }
            .task-input {
                width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #243048;
                background: #07090f; color: #fff; font-family: inherit; font-size: 12.5px;
                margin-top: 6px; margin-bottom: 8px;
            }
            .task-btn {
                width: 100%; padding: 8px; border-radius: 6px; border: none;
                background: var(--accent-blue); color: #000; font-weight: 700; font-size: 12px;
                cursor: pointer;
            }
            .preset-btn {
                background: #111726; border: 1px solid var(--card-border); color: #cbd5e1;
                font-size: 11px; padding: 6px 10px; border-radius: 6px; cursor: pointer;
                text-align: left; width: 100%; margin-top: 5px; transition: all 0.2s;
            }
            .preset-btn:hover { background: #1a2338; color: #fff; border-color: var(--accent-blue); }

            /* Agent Activity List */
            .agent-item {
                display: flex; justify-content: space-between; align-items: center;
                background: #090d17; border: 1px solid var(--card-border);
                border-radius: 8px; padding: 9px 12px; font-size: 12px; margin-bottom: 6px;
            }
            .agent-status-tag {
                font-size: 10.5px; font-weight: 700; padding: 2px 7px; border-radius: 4px;
            }

            /* 3D Viewport */
            #viewport-3d {
                position: relative; width: 100%; height: 100%; overflow: hidden;
            }
            #webgl-canvas { width: 100%; height: 100%; display: block; }

            /* Floating Floor HUD */
            .floor-hud {
                position: absolute; top: 16px; left: 16px; right: 16px;
                display: flex; justify-content: space-between; align-items: center;
                pointer-events: none; z-index: 10;
            }
            .hud-pill {
                background: rgba(9, 13, 23, 0.88); backdrop-filter: blur(10px);
                border: 1px solid var(--card-border); border-radius: 30px;
                padding: 7px 16px; font-size: 12px; font-weight: 700;
                display: flex; align-items: center; gap: 8px; pointer-events: auto;
            }

            /* Camera Preset Buttons (Bottom Overlay) */
            .camera-dock {
                position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                background: rgba(9, 13, 23, 0.9); backdrop-filter: blur(14px);
                border: 1px solid var(--card-border); border-radius: 30px;
                padding: 6px 12px; display: flex; gap: 6px; z-index: 10;
            }
            .dock-btn {
                background: transparent; border: none; color: var(--text-muted);
                padding: 6px 14px; border-radius: 20px; font-size: 11.5px; font-weight: 700;
                cursor: pointer; transition: all 0.2s;
            }
            .dock-btn.active, .dock-btn:hover { background: var(--accent-blue); color: #000; }

            /* Right Panel: Chat Stream */
            .chat-list {
                flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 8px;
                margin-top: 10px; padding-right: 4px;
            }
            .chat-bubble {
                background: #090e18; border: 1px solid var(--card-border);
                border-radius: 9px; padding: 10px 12px; font-size: 12px; line-height: 1.45;
                animation: slideUp 0.25s ease;
            }
            .chat-meta { display: flex; justify-content: space-between; font-size: 10.5px; color: var(--text-muted); margin-bottom: 3px; }
            .chat-author { font-weight: 700; color: var(--accent-blue); }
            @keyframes slideUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

            @media (max-width: 1080px) {
                .main-content { grid-template-columns: 270px 1fr 290px; }
            }
        </style>
    </head>
    <body>
        <div id="app-root">
            <!-- TOP APP BAR -->
            <header class="top-bar">
                <div class="brand-badge">
                    <span>🏢 AI Agent Virtual Office</span>
                    <span class="brand-pill">7 AGENTS ONLINE</span>
                </div>
                <nav class="top-nav">
                    <button class="nav-link active" onclick="setCameraView('overview')">Overview</button>
                    <button class="nav-link" onclick="setCameraView('walkin')">Walk In</button>
                    <button class="nav-link" onclick="setCameraView('trading')">Trading Floor</button>
                    <button class="nav-link" onclick="setCameraView('branding')">Media Studio</button>
                    <button class="nav-link" onclick="setCameraView('manager')">Manager Office</button>
                    <button class="nav-link" onclick="setCameraView('coffee')">Lounge & Coffee</button>
                </nav>
                <div class="top-right-status">
                    <div class="pulse-dot"></div>
                    <span id="exness-quick-badge" style="color: var(--accent-green); font-weight: 700;">Exness MT5: #434353249</span>
                </div>
            </header>

            <!-- THREE COLUMN CONTENT -->
            <main class="main-content">
                <!-- LEFT SIDEBAR -->
                <aside class="panel-left">
                    <!-- Metrics Row -->
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-label">Active Agents</div>
                            <div class="metric-val" style="color: var(--accent-green);">7 / 7</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Tasks Executed</div>
                            <div class="metric-val">32</div>
                        </div>
                    </div>

                    <!-- Exness Demo Card -->
                    <div class="exness-banner">
                        <div>
                            <div style="font-size: 10.5px; font-weight: 700; color: var(--accent-green); text-transform: uppercase;">Exness MT5 Trial7</div>
                            <div id="exness-bal-display" style="font-size: 20px; font-weight: 800; font-family: 'JetBrains Mono';">$20.21 USD</div>
                            <small style="color: var(--text-muted); font-size: 11px;">Account: #434353249 · 1:2000</small>
                        </div>
                        <button onclick="dispatchPresetTask('Sync Exness MT5 Balance & Orders')" style="background: rgba(16,185,129,0.2); border: 1px solid var(--accent-green); color: var(--accent-green); border-radius: 6px; padding: 6px 10px; font-weight: 700; font-size: 11px; cursor: pointer;">Sync</button>
                    </div>

                    <!-- Task Assignment -->
                    <div class="task-box">
                        <div style="font-size: 11.5px; font-weight: 800; color: var(--text-muted); text-transform: uppercase;">Command AI Workforce</div>
                        <input type="text" id="custom-task-input" class="task-input" placeholder="e.g. Scan BTC 4H Golden Pocket...">
                        <button class="task-btn" onclick="submitCustomTask()">▶ START DIRECTIVE</button>

                        <div style="margin-top: 10px; font-size: 11px; color: var(--text-muted); font-weight: 700;">QUICK DIRECTIVES:</div>
                        <button class="preset-btn" onclick="dispatchPresetTask('Execute SMC 4H Golden Pocket Scan')">⚡ Scan BTC 4H SMC Golden Pocket</button>
                        <button class="preset-btn" onclick="dispatchPresetTask('Draft Viral Twitter Breakdown Thread')">📢 Launch Viral Twitter Breakdown</button>
                        <button class="preset-btn" onclick="dispatchPresetTask('Send Team on 2-Minute Coffee Break')">☕ Send Team to Coffee Bar</button>
                    </div>

                    <!-- Agent Activity Roster -->
                    <div>
                        <div style="font-size: 11px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; margin-bottom: 8px;">Agent Activity</div>
                        <div id="agent-roster-container"></div>
                    </div>
                </aside>

                <!-- CENTER 3D VIEWPORT -->
                <div id="viewport-3d">
                    <div class="floor-hud">
                        <div class="hud-pill">
                            <span style="color: var(--text-muted);">MARKET:</span>
                            <span id="hud-btc" style="color: #fff; font-family: 'JetBrains Mono';">$65,000.00</span>
                            <span id="hud-trend" style="color: var(--accent-green);">BULLISH</span>
                        </div>
                        <div class="hud-pill">
                            <span style="color: var(--text-muted);">SMC ZONE:</span>
                            <span id="hud-zone" style="color: var(--accent-gold);">DISCOUNT (0.618 OTE)</span>
                        </div>
                    </div>

                    <canvas id="webgl-canvas"></canvas>

                    <!-- Camera Views Dock -->
                    <div class="camera-dock">
                        <button class="dock-btn active" onclick="setCameraView('overview')">Overview</button>
                        <button class="dock-btn" onclick="setCameraView('trading')">Trading Cluster</button>
                        <button class="dock-btn" onclick="setCameraView('branding')">Media Studio</button>
                        <button class="dock-btn" onclick="setCameraView('manager')">Manager Office</button>
                        <button class="dock-btn" onclick="setCameraView('coffee')">Coffee Bar</button>
                        <button class="dock-btn" onclick="setCameraView('wall')">Big LED Wall</button>
                    </div>
                </div>

                <!-- RIGHT SIDEBAR: AGENT COMMUNICATION (INTER-COM) -->
                <aside class="panel-right">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 10px;">
                        <div>
                            <div style="font-size: 12px; font-weight: 800; text-transform: uppercase;">Agent Communication</div>
                            <small style="color: var(--text-muted); font-size: 11px;">Internal Team Coordination</small>
                        </div>
                        <span class="brand-pill" style="color: var(--accent-green); background: rgba(16,185,129,0.15);">● LIVE</span>
                    </div>

                    <div class="chat-list" id="chat-stream-container"></div>

                    <!-- Bottom Trade Setup Tag -->
                    <div style="background: #090e18; border: 1px solid var(--card-border); border-radius: 8px; padding: 10px; margin-top: 10px; font-size: 11px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-muted);">Current Active Setup:</span>
                            <span style="color: var(--accent-green); font-weight: 700;">SETUP 3.1 (+1,026)</span>
                        </div>
                        <div style="margin-top: 4px; color: #cbd5e1;">Exness MT5: Auto-hedging enabled · 1% max risk shield active.</div>
                    </div>
                </aside>
            </main>
        </div>

        <!-- THREE.JS HIGH FIDELITY 3D OFFICE SCRIPT -->
        <script>
            let scene, camera, renderer, controls;
            let ledWallCanvas, ledWallTexture;
            let liveBalance = 20.21, btcDisplay = "$65,000.00";
            let agentObjects = [];

            function init3DWorld() {
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

                // Lighting
                const ambient = new THREE.AmbientLight(0xffffff, 0.6);
                scene.add(ambient);

                const sun = new THREE.DirectionalLight(0x38bdf8, 1.2);
                sun.position.set(25, 40, 20);
                sun.castShadow = true;
                scene.add(sun);

                // Floor with Perimeter Glowing Fence (from WhatsApp Video 2)
                createFloorAndPerimeter();

                // Huge Wall LED Screen (from Video 1 & 2)
                createLEDWall();

                // Cubicles & Desks
                createTradingCubicles(-8, -2);
                createMediaStudio(8, 2);
                createManagerOffice(-14, 10);
                createCoffeeLounge(12, 10);
                createServerFarm(-18, -10);

                window.addEventListener('resize', onWindowResize);
                animate();
            }

            // Floor & Glowing Golden Border Fence
            function createFloorAndPerimeter() {
                // Tiled floor
                const floorGeo = new THREE.PlaneGeometry(54, 44);
                const floorMat = new THREE.MeshStandardMaterial({ color: 0x090d18, roughness: 0.6, metalness: 0.3 });
                const floor = new THREE.Mesh(floorGeo, floorMat);
                floor.rotation.x = -Math.PI / 2;
                floor.receiveShadow = true;
                scene.add(floor);

                const grid = new THREE.GridHelper(54, 54, 0x1e293b, 0x0f172a);
                grid.position.y = 0.02;
                scene.add(grid);

                // Glowing Golden Glass Perimeter Railing (from Video 2)
                const fenceMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.85 });
                const railGeoX = new THREE.BoxGeometry(54, 0.1, 0.1);
                const railGeoZ = new THREE.BoxGeometry(0.1, 0.1, 44);

                const r1 = new THREE.Mesh(railGeoX, fenceMat); r1.position.set(0, 1.2, 22); scene.add(r1);
                const r2 = new THREE.Mesh(railGeoX, fenceMat); r2.position.set(0, 1.2, -22); scene.add(r2);
                const r3 = new THREE.Mesh(railGeoZ, fenceMat); r3.position.set(-27, 1.2, 0); scene.add(r3);
                const r4 = new THREE.Mesh(railGeoZ, fenceMat); r4.position.set(27, 1.2, 0); scene.add(r4);
            }

            // Big Wall Display
            function createLEDWall() {
                ledWallCanvas = document.createElement('canvas');
                ledWallCanvas.width = 1024;
                ledWallCanvas.height = 512;
                updateLEDWallCanvas();

                ledWallTexture = new THREE.CanvasTexture(ledWallCanvas);
                const wallGeo = new THREE.PlaneGeometry(28, 12);
                const wallMat = new THREE.MeshBasicMaterial({ map: ledWallTexture });
                const wall = new THREE.Mesh(wallGeo, wallMat);
                wall.position.set(0, 8.5, -21.8);
                scene.add(wall);
            }

            function updateLEDWallCanvas() {
                const ctx = ledWallCanvas.getContext('2d');
                ctx.fillStyle = '#03050a';
                ctx.fillRect(0, 0, 1024, 512);

                ctx.fillStyle = '#38bdf8';
                ctx.font = 'bold 34px "Plus Jakarta Sans"';
                ctx.fillText('EXNESS MT5 · INSTITUTIONAL TRADING FLOOR', 40, 60);

                ctx.fillStyle = '#94a3b8';
                ctx.font = '20px "JetBrains Mono"';
                ctx.fillText('ACCOUNT #434353249 · Exness-MT5Trial7 (HEDGING)', 40, 95);

                ctx.fillStyle = '#10b981';
                ctx.font = 'bold 68px "JetBrains Mono"';
                ctx.fillText(`US$ ${liveBalance.toLocaleString('en-US', {minimumFractionDigits: 2})}`, 40, 175);

                // Setup badge tags (like Video 2)
                ctx.fillStyle = '#f59e0b';
                ctx.font = 'bold 22px "JetBrains Mono"';
                ctx.fillText('SETUP 3.1: 0.618 OTE (+1,026)', 40, 220);

                ctx.fillStyle = '#38bdf8';
                ctx.fillText(`BTC TICKER: ${btcDisplay} · TREND: BULLISH`, 480, 220);

                // Green Equity Chart Line
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.moveTo(40, 440);
                ctx.lineTo(180, 410);
                ctx.lineTo(340, 430);
                ctx.lineTo(500, 340);
                ctx.lineTo(660, 360);
                ctx.lineTo(820, 260);
                ctx.lineTo(980, 240);
                ctx.stroke();

                ctx.fillStyle = 'rgba(16, 185, 129, 0.12)';
                ctx.lineTo(980, 480);
                ctx.lineTo(40, 480);
                ctx.closePath();
                ctx.fill();

                if (ledWallTexture) ledWallTexture.needsUpdate = true;
            }

            // Trading Cubicles (Left Wing)
            function createTradingCubicles(x, z) {
                const group = new THREE.Group();
                group.position.set(x, 0, z);

                // Double pod desks
                for (let row = 0; row < 2; row++) {
                    const desk = new THREE.Mesh(
                        new THREE.BoxGeometry(10, 1.4, 3.4),
                        new THREE.MeshStandardMaterial({ color: 0x111726, roughness: 0.4 })
                    );
                    desk.position.set(0, 1.4, row * 5);
                    group.add(desk);

                    // Monitors on desk
                    for (let m = -1; m <= 1; m++) {
                        const screen = new THREE.Mesh(
                            new THREE.BoxGeometry(2.2, 1.3, 0.1),
                            new THREE.MeshBasicMaterial({ color: 0x0284c7 })
                        );
                        screen.position.set(m * 2.8, 2.8, (row * 5) - 0.6);
                        group.add(screen);

                        // Office Chair
                        const chair = new THREE.Mesh(
                            new THREE.CylinderGeometry(0.5, 0.5, 1.2),
                            new THREE.MeshStandardMaterial({ color: 0x1e293b })
                        );
                        chair.position.set(m * 2.8, 0.7, (row * 5) + 1.2);
                        group.add(chair);

                        // 3D Robot Agent (Trading Agents)
                        const name = row === 0 ? (m === -1 ? "Alex" : (m === 0 ? "David" : "Marcus")) : "Leo";
                        createAgentAvatar(group, m * 2.8, 0.8, (row * 5) + 1.2, 0x38bdf8, name);
                    }
                }
                scene.add(group);
            }

            // Media Studio (Right Wing)
            function createMediaStudio(x, z) {
                const group = new THREE.Group();
                group.position.set(x, 0, z);

                // Studio desk
                const desk = new THREE.Mesh(
                    new THREE.BoxGeometry(9, 1.4, 3.4),
                    new THREE.MeshStandardMaterial({ color: 0x1a1226, roughness: 0.4 })
                );
                desk.position.set(0, 1.4, 0);
                group.add(desk);

                // Neon Purple Monitors
                for (let m = -1; m <= 1; m++) {
                    const screen = new THREE.Mesh(
                        new THREE.BoxGeometry(2.2, 1.3, 0.1),
                        new THREE.MeshBasicMaterial({ color: 0xa855f7 })
                    );
                    screen.position.set(m * 2.6, 2.8, -0.6);
                    group.add(screen);

                    const name = m === -1 ? "Sophia" : (m === 0 ? "Mia" : "Noah");
                    createAgentAvatar(group, m * 2.6, 0.8, 1.2, 0xa855f7, name);
                }

                // Whiteboard / Glass Board
                const board = new THREE.Mesh(
                    new THREE.BoxGeometry(6, 4, 0.1),
                    new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.2 })
                );
                board.position.set(0, 3.5, 4);
                group.add(board);

                scene.add(group);
            }

            // Manager Office with Golden Trophy (from Video 1 Frame 7)
            function createManagerOffice(x, z) {
                const group = new THREE.Group();
                group.position.set(x, 0, z);

                // Mahogany Executive Desk
                const desk = new THREE.Mesh(
                    new THREE.BoxGeometry(6, 1.5, 3.2),
                    new THREE.MeshStandardMaterial({ color: 0x3b1c11, roughness: 0.5 })
                );
                desk.position.y = 1.4;
                group.add(desk);

                // Golden Trophy on desk (exact from video!)
                const trophyCup = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.35, 0.15, 0.7),
                    new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8, roughness: 0.2 })
                );
                trophyCup.position.set(-1.6, 2.5, 0.4);
                group.add(trophyCup);

                // Executive Bookshelf behind desk
                const shelf = new THREE.Mesh(
                    new THREE.BoxGeometry(7, 6, 1),
                    new THREE.MeshStandardMaterial({ color: 0x1f2937 })
                );
                shelf.position.set(0, 3.5, -3);
                group.add(shelf);

                scene.add(group);
            }

            // Coffee Bar & Lounge (from Video 1)
            function createCoffeeLounge(x, z) {
                const group = new THREE.Group();
                group.position.set(x, 0, z);

                // Coffee Counter
                const counter = new THREE.Mesh(
                    new THREE.BoxGeometry(7, 1.6, 2.2),
                    new THREE.MeshStandardMaterial({ color: 0x18181b })
                );
                counter.position.y = 1.4;
                group.add(counter);

                // Coffee Machine on counter
                const machine = new THREE.Mesh(
                    new THREE.BoxGeometry(1.2, 1.1, 0.9),
                    new THREE.MeshStandardMaterial({ color: 0xef4444 })
                );
                machine.position.set(-1.8, 2.7, 0);
                group.add(machine);

                // Lounge Couch
                const couch = new THREE.Mesh(
                    new THREE.BoxGeometry(6, 1.2, 2.2),
                    new THREE.MeshStandardMaterial({ color: 0x1e3a5f })
                );
                couch.position.set(0, 0.8, 4);
                group.add(couch);

                scene.add(group);
            }

            // Server Farm Racks
            function createServerFarm(x, z) {
                for (let i = 0; i < 3; i++) {
                    const rack = new THREE.Mesh(
                        new THREE.BoxGeometry(2.4, 7.5, 2.2),
                        new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.8 })
                    );
                    rack.position.set(x + (i * 3), 3.75, z);
                    scene.add(rack);

                    // Blinking LED Strip
                    const led = new THREE.Mesh(
                        new THREE.BoxGeometry(1.8, 0.08, 0.05),
                        new THREE.MeshBasicMaterial({ color: i === 1 ? 0x10b981 : 0x38bdf8 })
                    );
                    led.position.set(x + (i * 3), 5.5, z + 1.12);
                    scene.add(led);
                }
            }

            // 3D Agent Model with Floating Name Badge
            function createAgentAvatar(parent, x, y, z, colorHex, name) {
                const agent = new THREE.Group();
                agent.position.set(x, y, z);

                // Body
                const body = new THREE.Mesh(
                    new THREE.BoxGeometry(0.85, 1.1, 0.65),
                    new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.5 })
                );
                body.position.y = 1.1;
                agent.add(body);

                // Head
                const head = new THREE.Mesh(
                    new THREE.BoxGeometry(0.65, 0.6, 0.6),
                    new THREE.MeshStandardMaterial({ color: 0x0f172a })
                );
                head.position.y = 2.0;
                agent.add(head);

                // Glowing Visor
                const visor = new THREE.Mesh(
                    new THREE.BoxGeometry(0.5, 0.16, 0.05),
                    new THREE.MeshBasicMaterial({ color: colorHex })
                );
                visor.position.set(0, 2.0, 0.31);
                agent.add(visor);

                parent.add(agent);
            }

            // Camera Presets
            function setCameraView(view) {
                document.querySelectorAll('.dock-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.nav-link').forEach(b => b.classList.remove('active'));
                
                if (view === 'overview') {
                    camera.position.set(32, 26, 32);
                    controls.target.set(0, 2, 0);
                } else if (view === 'walkin') {
                    camera.position.set(0, 3.5, 16);
                    controls.target.set(0, 3, -10);
                } else if (view === 'trading') {
                    camera.position.set(-8, 9, 7);
                    controls.target.set(-8, 2, -2);
                } else if (view === 'branding') {
                    camera.position.set(8, 9, 10);
                    controls.target.set(8, 2, 2);
                } else if (view === 'manager') {
                    camera.position.set(-14, 8, 17);
                    controls.target.set(-14, 2, 10);
                } else if (view === 'coffee') {
                    camera.position.set(12, 8, 16);
                    controls.target.set(12, 2, 10);
                } else if (view === 'wall') {
                    camera.position.set(0, 10, 8);
                    controls.target.set(0, 8.5, -21.8);
                }
            }

            function onWindowResize() {
                const container = document.getElementById('viewport-3d');
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }

            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }

            // TASK & SYNC ENGINE
            async function submitCustomTask() {
                const input = document.getElementById('custom-task-input');
                const text = input.value.trim();
                if (!text) return;
                input.value = '';
                await fetch('/api/task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ task: text })
                });
                syncTelemetry();
            }

            async function dispatchPresetTask(directive) {
                await fetch('/api/task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ task: directive })
                });
                syncTelemetry();
            }

            async function syncTelemetry() {
                try {
                    const res = await fetch('/api/telemetry');
                    const d = await res.json();

                    // Update Exness Balance & LED Wall
                    if (d.exness) {
                        liveBalance = d.exness.balance;
                        document.getElementById('exness-bal-display').innerText = `$${liveBalance.toLocaleString('en-US', {minimumFractionDigits: 2})} USD`;
                        document.getElementById('exness-quick-badge').innerText = `Exness MT5: #${d.exness.account_id} (${d.exness.server})`;
                    }

                    // Market
                    if (d.market_analysis && d.market_analysis.current_price) {
                        btcDisplay = `$${d.market_analysis.current_price.toLocaleString()}`;
                        document.getElementById('hud-btc').innerText = btcDisplay;
                        document.getElementById('hud-trend').innerText = d.market_analysis.trend;
                        document.getElementById('hud-trend').style.color = d.market_analysis.trend === 'BULLISH' ? 'var(--accent-green)' : 'var(--accent-red)';
                        document.getElementById('hud-zone').innerText = d.market_analysis.zone_status;
                    }

                    // Update Canvas on 3D LED Screen
                    updateLEDWallCanvas();

                    // Agent Roster
                    if (d.agents) {
                        document.getElementById('agent-roster-container').innerHTML = d.agents.map(a => `
                            <div class="agent-item">
                                <div>
                                    <strong style="color: ${a.color}">${a.name}</strong>
                                    <small style="color: var(--text-muted); display:block;">${a.role}</small>
                                </div>
                                <span class="agent-status-tag" style="background: rgba(255,255,255,0.06); color: ${a.color};">${a.status}</span>
                            </div>
                        `).join('');
                    }

                    // Inter-Com Chat Stream
                    if (d.agent_messages) {
                        document.getElementById('chat-stream-container').innerHTML = d.agent_messages.map(m => `
                            <div class="chat-bubble">
                                <div class="chat-meta">
                                    <span class="chat-author">${m.agent} (${m.role})</span>
                                    <span>${m.time}</span>
                                </div>
                                <div>${m.text}</div>
                            </div>
                        `).join('');
                    }
                } catch(e) {}
            }

            window.onload = () => {
                init3DWorld();
                syncTelemetry();
                setInterval(syncTelemetry, 3000);
            };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
