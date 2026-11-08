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
    orchestrator.send_agent_message("Leo", "Execution Trader", f"Exness Demo Linked! Account #{data.account_id} on {data.server} ($ {data.balance:,.2f})")
    return {"status": "success", "exness": res}

@app.get("/", response_class=HTMLResponse)
def virtual_office_app():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>3D Virtual AI Trading Floor & Media Office</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <!-- Three.js & OrbitControls for 3D Virtual Office -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            :root {
                --bg: #05070d;
                --panel: rgba(13, 18, 30, 0.92);
                --border: #1a2438;
                --accent-blue: #38bdf8;
                --accent-green: #10b981;
                --accent-gold: #f59e0b;
                --accent-purple: #a855f7;
                --accent-red: #f43f5e;
                --text: #f1f5f9;
                --muted: #8494ab;
            }
            * { box-sizing: border-box; }
            body, html {
                margin: 0; padding: 0; width: 100%; height: 100%;
                overflow: hidden; background: var(--bg); color: var(--text);
                font-family: 'Plus Jakarta Sans', sans-serif;
            }

            /* Main Layout Grid */
            #app-layout {
                display: grid;
                grid-template-columns: 320px 1fr 340px;
                width: 100vw; height: 100vh;
                position: relative;
            }

            /* Left & Right Sidebars */
            .sidebar {
                background: var(--panel);
                backdrop-filter: blur(16px);
                border-right: 1px solid var(--border);
                display: flex; flex-direction: column;
                z-index: 10; padding: 18px;
                overflow-y: auto; height: 100vh;
            }
            .sidebar-right {
                border-right: none;
                border-left: 1px solid var(--border);
            }

            /* 3D Viewport */
            #canvas-container {
                position: relative;
                width: 100%; height: 100%;
                overflow: hidden;
            }
            #webgl-canvas { width: 100%; height: 100%; display: block; }

            /* HUD Floating Over 3D Canvas */
            .hud-overlay {
                position: absolute; top: 16px; left: 16px; right: 16px;
                display: flex; justify-content: space-between; align-items: center;
                pointer-events: none; z-index: 20;
            }
            .hud-card {
                background: rgba(10, 15, 26, 0.85);
                backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: 12px; padding: 10px 18px;
                pointer-events: auto; display: flex; align-items: center; gap: 14px;
            }
            .cam-controls {
                position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                display: flex; gap: 8px; z-index: 20; background: rgba(10,15,26,0.88);
                padding: 6px; border-radius: 30px; border: 1px solid var(--border);
            }
            .cam-btn {
                background: transparent; border: none; color: var(--muted);
                padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;
                cursor: pointer; transition: all 0.2s;
            }
            .cam-btn.active, .cam-btn:hover { background: var(--accent-blue); color: #000; }

            /* Typography & Cards */
            .brand-header h2 { margin: 0; font-size: 17px; font-weight: 800; display: flex; align-items: center; gap: 8px; }
            .brand-header p { margin: 4px 0 16px 0; font-size: 12px; color: var(--muted); }
            .section-label { font-size: 11px; font-weight: 800; color: var(--muted); text-transform: uppercase; letter-spacing: 0.8px; margin: 16px 0 8px 0; }
            
            .stat-box {
                background: #080c14; border: 1px solid var(--border); border-radius: 10px;
                padding: 12px 14px; margin-bottom: 10px;
            }
            .stat-title { font-size: 11px; color: var(--muted); text-transform: uppercase; }
            .stat-val { font-size: 20px; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin: 4px 0; }

            .badge {
                padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;
                display: inline-flex; align-items: center; gap: 6px;
            }
            .badge-green { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
            .badge-gold { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }

            /* Agent Roster List */
            .agent-row {
                display: flex; align-items: center; justify-content: space-between;
                background: #080c14; border: 1px solid var(--border); border-radius: 8px;
                padding: 10px; margin-bottom: 8px; font-size: 12px;
            }
            .agent-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }

            /* Agent Chat Stream (Right Sidebar) */
            .chat-stream {
                flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 10px;
                padding-right: 4px; font-size: 12.5px;
            }
            .chat-msg {
                background: #080c14; border: 1px solid var(--border); border-radius: 10px;
                padding: 10px 12px; line-height: 1.45; animation: fadeIn 0.3s ease;
            }
            .chat-meta { display: flex; justify-content: space-between; font-size: 10.5px; color: var(--muted); margin-bottom: 4px; }
            .chat-author { font-weight: 700; color: var(--accent-blue); }
            .chat-text { color: #cbd5e1; }
            @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

            /* Buttons & Modal */
            .btn-action {
                width: 100%; padding: 10px; border-radius: 8px; border: none;
                background: var(--accent-blue); color: #000; font-weight: 700; font-size: 12.5px;
                cursor: pointer; transition: opacity 0.2s; margin-top: 6px;
            }
            .btn-action:hover { opacity: 0.9; }

            .modal-bg {
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0,0,0,0.75); backdrop-filter: blur(8px);
                display: none; align-items: center; justify-content: center; z-index: 1000;
            }
            .modal-card {
                background: #0e1320; border: 1px solid var(--border); border-radius: 14px;
                padding: 24px; width: 420px; box-shadow: 0 20px 50px rgba(0,0,0,0.8);
            }
            .input-group { margin-bottom: 14px; }
            .input-group label { display: block; font-size: 11.5px; font-weight: 700; color: var(--muted); margin-bottom: 5px; }
            .input-group input, .input-group select {
                width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border);
                background: #070a12; color: #fff; font-family: inherit; font-size: 13px;
            }

            @media (max-width: 1024px) {
                #app-layout { grid-template-columns: 280px 1fr 280px; }
            }
        </style>
    </head>
    <body>
        <div id="app-layout">
            <!-- LEFT SIDEBAR: INSTITUTIONAL CONTROL -->
            <div class="sidebar">
                <div class="brand-header">
                    <h2>🏛️ AI Trading Floor</h2>
                    <p>Proprietary SMC Desk & Media Studio</p>
                </div>

                <div class="stat-box">
                    <div class="stat-title">Exness Demo Balance</div>
                    <div id="acc-balance" class="stat-val">$50,000.00</div>
                    <div id="exness-tag" class="badge badge-gold">Exness: Standby</div>
                </div>

                <button class="btn-action" onclick="openExnessModal()">⚙️ Link Exness MT5 Demo</button>

                <div class="section-label">Active Market Pulse</div>
                <div class="stat-box" style="margin-bottom: 6px;">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="stat-title">BTC/USDT</span>
                        <span id="btc-chg" style="color: var(--accent-green); font-size: 11px; font-weight: 700;">+0.00%</span>
                    </div>
                    <div id="btc-price" class="stat-val" style="font-size: 18px;">$65,000.00</div>
                    <div style="font-size: 11.5px; color: var(--muted); margin-top: 4px;">
                        Trend: <strong id="htf-trend" style="color: var(--accent-green);">BULLISH</strong> | 
                        Zone: <strong id="eq-zone" style="color: var(--accent-gold);">DISCOUNT</strong>
                    </div>
                </div>

                <div class="section-label">Workforce Status (7/7 Online)</div>
                <div id="agent-roster"></div>
            </div>

            <!-- CENTER: 3D VIRTUAL OFFICE FLOOR -->
            <div id="canvas-container">
                <div class="hud-overlay">
                    <div class="hud-card">
                        <span style="font-size: 12px; font-weight: 700; color: var(--muted);">FLOOR STATUS:</span>
                        <span class="badge badge-green">● 7 AGENTS ACTIVE</span>
                    </div>
                    <div class="hud-card">
                        <span style="font-size: 12px; font-weight: 700; color: var(--muted);">SMC SETUP:</span>
                        <span id="hud-setup-badge" style="font-size: 12px; font-weight: 700; color: var(--accent-blue);">0.618 Golden Pocket Active</span>
                    </div>
                </div>

                <!-- 3D Canvas -->
                <canvas id="webgl-canvas"></canvas>

                <!-- Camera Switcher -->
                <div class="cam-controls">
                    <button class="cam-btn active" onclick="setCameraView('iso')">Isometric Floor</button>
                    <button class="cam-btn" onclick="setCameraView('trading')">Trading Desk</button>
                    <button class="cam-btn" onclick="setCameraView('branding')">Media Studio</button>
                    <button class="cam-btn" onclick="setCameraView('wall')">LED Wall</button>
                </div>
            </div>

            <!-- RIGHT SIDEBAR: REAL-TIME AGENT COMMUNICATION (INTER-COM) -->
            <div class="sidebar sidebar-right">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <div class="section-label" style="margin: 0;">Agent Inter-Com</div>
                    <span class="badge badge-green" style="font-size: 10px;">LIVE CHAT</span>
                </div>
                <div style="font-size: 11.5px; color: var(--muted); margin-bottom: 12px;">
                    Autonomous coordination between Quant Desk & Media Division.
                </div>

                <!-- Live Chat Feed -->
                <div class="chat-stream" id="chat-stream">
                    <div class="chat-msg">
                        <div class="chat-meta"><span class="chat-author">System</span><span>00:00</span></div>
                        <div class="chat-text">Connecting to 3D Virtual Trading Floor inter-com stream...</div>
                    </div>
                </div>

                <div class="section-label" style="margin-top: 16px;">Latest Branding Post</div>
                <div id="latest-brand-card" style="background:#080c14; border:1px solid var(--border); border-radius:8px; padding:10px; font-size:11.5px;">
                    <div style="color: var(--accent-purple); font-weight: 700; margin-bottom: 4px;">Twitter / X Thread</div>
                    <div id="latest-brand-text" style="color: #cbd5e1; line-height: 1.4;">Analyzing SMC footprint...</div>
                </div>
            </div>
        </div>

        <!-- EXNESS MODAL -->
        <div id="exness-modal" class="modal-bg">
            <div class="modal-card">
                <h3 style="margin-top:0; color:#fff;">⚙️ Connect Exness MT5 Demo</h3>
                <p style="font-size:12px; color:var(--muted); margin-bottom:16px;">Link your Exness demo account to route autonomous SMC trades.</p>
                <div class="input-group">
                    <label>Exness Login ID</label>
                    <input type="text" id="ex-acc-id" placeholder="e.g. 142859102">
                </div>
                <div class="input-group">
                    <label>Server</label>
                    <select id="ex-server">
                        <option value="Exness-MT5Trial">Exness-MT5Trial</option>
                        <option value="Exness-MT5Trial2">Exness-MT5Trial2</option>
                        <option value="Exness-MT5Trial9">Exness-MT5Trial9</option>
                        <option value="Exness-MT4Trial">Exness-MT4Trial</option>
                    </select>
                </div>
                <div class="input-group">
                    <label>Demo Capital (USD)</label>
                    <input type="number" id="ex-balance" value="50000">
                </div>
                <div style="display:flex; gap:10px; margin-top:18px;">
                    <button class="btn-action" onclick="submitExness()" style="margin:0;">Connect</button>
                    <button class="btn-action" onclick="closeExnessModal()" style="background:transparent; border:1px solid var(--border); color:#fff; margin:0;">Cancel</button>
                </div>
            </div>
        </div>

        <!-- THREE.JS 3D VIRTUAL OFFICE SCRIPT -->
        <script>
            let scene, camera, renderer, controls;
            let wallDisplayCanvas, wallDisplayTexture;
            let currentEquity = 50000.0, currentBTC = "$65,000.00";

            function init3DOffice() {
                const container = document.getElementById('canvas-container');
                const width = container.clientWidth;
                const height = container.clientHeight;

                // 1. Scene & Camera
                scene = new THREE.Scene();
                scene.background = new THREE.Color(0x05070d);
                scene.fog = new THREE.FogExp2(0x05070d, 0.018);

                camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
                camera.position.set(28, 22, 28);

                // 2. Renderer
                renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('webgl-canvas'), antialias: true });
                renderer.setSize(width, height);
                renderer.setPixelRatio(window.devicePixelRatio);
                renderer.shadowMap.enabled = true;

                // 3. Controls
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                controls.maxPolarAngle = Math.PI / 2.1;
                controls.target.set(0, 2, 0);

                // 4. Lighting
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.55);
                scene.add(ambientLight);

                const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
                dirLight.position.set(20, 35, 15);
                dirLight.castShadow = true;
                scene.add(dirLight);

                // Neon accent point lights
                const neonGreen = new THREE.PointLight(0x10b981, 2, 30);
                neonGreen.position.set(-6, 8, -6);
                scene.add(neonGreen);

                const neonPurple = new THREE.PointLight(0xa855f7, 2, 30);
                neonPurple.position.set(8, 8, 4);
                scene.add(neonPurple);

                // 5. Floor Grid
                const floorGeo = new THREE.PlaneGeometry(50, 40);
                const floorMat = new THREE.MeshStandardMaterial({ color: 0x0a0f1d, roughness: 0.7, metalness: 0.2 });
                const floor = new THREE.Mesh(floorGeo, floorMat);
                floor.rotation.x = -Math.PI / 2;
                floor.receiveShadow = true;
                scene.add(floor);

                const grid = new THREE.GridHelper(50, 50, 0x1e293b, 0x0f172a);
                grid.position.y = 0.02;
                scene.add(grid);

                // 6. Giant Wall Display (Back Wall)
                createWallDisplay();

                // 7. Trading Desks Cluster (Left Side)
                createDeskCluster(-7, -2, "TRADING FLOOR", 0x38bdf8);

                // 8. Media & Branding Desks Cluster (Right Side)
                createDeskCluster(7, 3, "BRANDING STUDIO", 0xa855f7);

                // 9. Server Racks (Exness Bridge Gateway)
                createServerRacks(-15, -12);

                // Resize listener
                window.addEventListener('resize', onWindowResize);
                animate();
            }

            // Create Canvas-based Wall Display Texture
            function createWallDisplay() {
                wallDisplayCanvas = document.createElement('canvas');
                wallDisplayCanvas.width = 1024;
                wallDisplayCanvas.height = 512;
                updateWallDisplayCanvas();

                wallDisplayTexture = new THREE.CanvasTexture(wallDisplayCanvas);
                const screenGeo = new THREE.PlaneGeometry(24, 11);
                const screenMat = new THREE.MeshBasicMaterial({ map: wallDisplayTexture });
                const screen = new THREE.Mesh(screenGeo, screenMat);
                screen.position.set(0, 9, -18);
                scene.add(screen);

                // Glowing border
                const borderGeo = new THREE.BoxGeometry(24.4, 11.4, 0.4);
                const borderMat = new THREE.MeshStandardMaterial({ color: 0x111827, emissive: 0x10b981, emissiveIntensity: 0.25 });
                const borderMesh = new THREE.Mesh(borderGeo, borderMat);
                borderMesh.position.set(0, 9, -18.3);
                scene.add(borderMesh);
            }

            function updateWallDisplayCanvas() {
                const ctx = wallDisplayCanvas.getContext('2d');
                ctx.fillStyle = '#050811';
                ctx.fillRect(0, 0, 1024, 512);

                // Title & Tickers
                ctx.fillStyle = '#38bdf8';
                ctx.font = 'bold 36px "Plus Jakarta Sans"';
                ctx.fillText('INSTITUTIONAL QUANT DESK · EXNESS MT5', 40, 60);

                ctx.fillStyle = '#94a3b8';
                ctx.font = '22px "JetBrains Mono"';
                ctx.fillText('REAL-TIME PORTFOLIO EQUITY CURVE', 40, 100);

                ctx.fillStyle = '#10b981';
                ctx.font = 'bold 64px "JetBrains Mono"';
                ctx.fillText(`$${currentEquity.toLocaleString('en-US', {minimumFractionDigits: 2})}`, 40, 175);

                ctx.fillStyle = '#38bdf8';
                ctx.font = '24px "JetBrains Mono"';
                ctx.fillText(`BTC TICKER: ${currentBTC} (HTF: BULLISH)`, 40, 220);

                // Glowing Green Chart Line
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 6;
                ctx.beginPath();
                ctx.moveTo(40, 440);
                ctx.lineTo(200, 420);
                ctx.lineTo(360, 450);
                ctx.lineTo(520, 360);
                ctx.lineTo(680, 380);
                ctx.lineTo(840, 290);
                ctx.lineTo(980, 270);
                ctx.stroke();

                ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
                ctx.lineTo(980, 480);
                ctx.lineTo(40, 480);
                ctx.closePath();
                ctx.fill();

                if (wallDisplayTexture) wallDisplayTexture.needsUpdate = true;
            }

            // Create Desk Pods with Multi-monitors and Agents
            function createDeskCluster(x, z, label, accentColor) {
                const group = new THREE.Group();
                group.position.set(x, 0, z);

                // Desk Surface
                const deskGeo = new THREE.BoxGeometry(9, 1.4, 4);
                const deskMat = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.4 });
                const desk = new THREE.Mesh(deskGeo, deskMat);
                desk.position.y = 1.4;
                desk.castShadow = true;
                group.add(desk);

                // Desk Accent Strip
                const stripGeo = new THREE.BoxGeometry(9.1, 0.1, 0.1);
                const stripMat = new THREE.MeshBasicMaterial({ color: accentColor });
                const strip = new THREE.Mesh(stripGeo, stripMat);
                strip.position.set(0, 2.1, 2);
                group.add(strip);

                // 3 Monitors
                for (let i = -1; i <= 1; i++) {
                    const monGeo = new THREE.BoxGeometry(2.2, 1.4, 0.1);
                    const monMat = new THREE.MeshBasicMaterial({ color: 0x0284c7 });
                    const mon = new THREE.Mesh(monGeo, monMat);
                    mon.position.set(i * 2.6, 2.9, -0.6);
                    group.add(mon);

                    // Monitor Stand
                    const standGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.8);
                    const standMat = new THREE.MeshStandardMaterial({ color: 0x334155 });
                    const stand = new THREE.Mesh(standGeo, standMat);
                    stand.position.set(i * 2.6, 2.4, -0.6);
                    group.add(stand);

                    // Stylized Robot Agent Seated
                    createRobotAgent(group, i * 2.6, 0.7, 1.4, accentColor);
                }

                scene.add(group);
            }

            // Stylized 3D Robot Agent
            function createRobotAgent(parent, x, y, z, colorHex) {
                const agent = new THREE.Group();
                agent.position.set(x, y, z);

                // Body
                const bodyGeo = new THREE.BoxGeometry(0.9, 1.1, 0.7);
                const bodyMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.5 });
                const body = new THREE.Mesh(bodyGeo, bodyMat);
                body.position.y = 1.2;
                agent.add(body);

                // Head with glowing visor
                const headGeo = new THREE.BoxGeometry(0.7, 0.6, 0.6);
                const headMat = new THREE.MeshStandardMaterial({ color: 0x0f172a });
                const head = new THREE.Mesh(headGeo, headMat);
                head.position.y = 2.1;
                agent.add(head);

                const visorGeo = new THREE.BoxGeometry(0.55, 0.18, 0.05);
                const visorMat = new THREE.MeshBasicMaterial({ color: colorHex });
                const visor = new THREE.Mesh(visorGeo, visorMat);
                visor.position.set(0, 2.1, 0.31);
                agent.add(visor);

                parent.add(agent);
            }

            // Server Racks (Gateway)
            function createServerRacks(x, z) {
                const rackGeo = new THREE.BoxGeometry(2.4, 7, 2);
                const rackMat = new THREE.MeshStandardMaterial({ color: 0x090d16, roughness: 0.8 });
                for (let i = 0; i < 3; i++) {
                    const rack = new THREE.Mesh(rackGeo, rackMat);
                    rack.position.set(x + (i * 3.2), 3.5, z);
                    scene.add(rack);

                    // Blinking LED Strip
                    const ledGeo = new THREE.BoxGeometry(1.8, 0.08, 0.05);
                    const ledMat = new THREE.MeshBasicMaterial({ color: i === 1 ? 0x10b981 : 0x38bdf8 });
                    const led = new THREE.Mesh(ledGeo, ledMat);
                    led.position.set(x + (i * 3.2), 5, z + 1.02);
                    scene.add(led);
                }
            }

            function setCameraView(view) {
                document.querySelectorAll('.cam-btn').forEach(b => b.classList.remove('active'));
                event.target.classList.add('active');

                if (view === 'iso') {
                    gsapAnimateCam(28, 22, 28, 0, 2, 0);
                } else if (view === 'trading') {
                    gsapAnimateCam(-6, 9, 8, -7, 2, -2);
                } else if (view === 'branding') {
                    gsapAnimateCam(9, 9, 14, 7, 2, 3);
                } else if (view === 'wall') {
                    gsapAnimateCam(0, 10, 12, 0, 9, -18);
                }
            }

            function gsapAnimateCam(x, y, z, tx, ty, tz) {
                camera.position.set(x, y, z);
                controls.target.set(tx, ty, tz);
            }

            function onWindowResize() {
                const container = document.getElementById('canvas-container');
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }

            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                renderer.render(scene, camera);
            }

            // API & SYNC LOGIC
            function openExnessModal() { document.getElementById('exness-modal').style.display = 'flex'; }
            function closeExnessModal() { document.getElementById('exness-modal').style.display = 'none'; }

            async function submitExness() {
                const accId = document.getElementById('ex-acc-id').value;
                const server = document.getElementById('ex-server').value;
                const bal = parseFloat(document.getElementById('ex-balance').value) || 50000;
                if (!accId) { alert('Enter Exness Login ID'); return; }

                await fetch('/api/exness/connect', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ account_id: accId, server: server, balance: bal })
                });
                closeExnessModal();
                syncTelemetry();
            }

            async function syncTelemetry() {
                try {
                    const res = await fetch('/api/telemetry');
                    const d = await res.json();

                    // Update Balance
                    currentEquity = d.account.equity;
                    document.getElementById('acc-balance').innerText = '$' + d.account.equity.toLocaleString('en-US', {minimumFractionDigits: 2});
                    
                    // Exness
                    if (d.exness && d.exness.connected) {
                        document.getElementById('exness-tag').innerText = `Exness: #${d.exness.account_id} (${d.exness.server})`;
                        document.getElementById('exness-tag').className = 'badge badge-green';
                    }

                    // Market
                    const m = d.market_analysis;
                    if (m && m.current_price) {
                        currentBTC = `$${m.current_price.toLocaleString()}`;
                        document.getElementById('btc-price').innerText = currentBTC;
                        document.getElementById('btc-chg').innerText = `${m.change_pct >= 0 ? '+' : ''}${m.change_pct.toFixed(2)}%`;
                        document.getElementById('btc-chg').style.color = m.change_pct >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
                        document.getElementById('htf-trend').innerText = m.trend;
                        document.getElementById('htf-trend').style.color = m.trend === 'BULLISH' ? 'var(--accent-green)' : 'var(--accent-red)';
                        document.getElementById('eq-zone').innerText = m.zone_status.includes('DISCOUNT') ? 'DISCOUNT (BUY)' : 'PREMIUM (SELL)';
                    }

                    // Update 3D LED Wall
                    updateWallDisplayCanvas();

                    // Workforce Roster
                    if (d.agents) {
                        document.getElementById('agent-roster').innerHTML = d.agents.map(a => `
                            <div class="agent-row">
                                <div>
                                    <span class="agent-dot" style="background: ${a.color}"></span>
                                    <strong>${a.name}</strong> <small style="color:var(--muted)">(${a.role.split(' ')[0]})</small>
                                </div>
                                <span style="font-size:10px; color:${a.color}; font-weight:700;">${a.status}</span>
                            </div>
                        `).join('');
                    }

                    // Inter-Com Chat Stream
                    if (d.agent_messages && d.agent_messages.length > 0) {
                        document.getElementById('chat-stream').innerHTML = d.agent_messages.map(msg => `
                            <div class="chat-msg">
                                <div class="chat-meta">
                                    <span class="chat-author">${msg.agent} (${msg.role})</span>
                                    <span>${msg.time}</span>
                                </div>
                                <div class="chat-text">${msg.text}</div>
                            </div>
                        `).join('');
                    }

                    // Latest Branding Post
                    if (d.branding_posts && d.branding_posts.length > 0) {
                        const lp = d.branding_posts[0];
                        document.getElementById('latest-brand-text').innerText = lp.headline;
                    }

                } catch(e) {}
            }

            window.onload = () => {
                init3DOffice();
                syncTelemetry();
                setInterval(syncTelemetry, 3500);
            };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
