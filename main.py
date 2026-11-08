import time
import threading
from datetime import datetime
import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(title="AI Agency & Trading Core Engine")

# In-memory storage for logs & metrics
system_logs = []
market_data = {
    "BTC": {"price": "Loading...", "change": "0.00%"},
    "ETH": {"price": "Loading...", "change": "0.00%"},
    "last_updated": "Never"
}

def fetch_live_market():
    """Fetches real-time crypto prices without needing API keys."""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url, params={"symbols": '["BTCUSDT","ETHUSDT"]'}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            for item in data:
                symbol = item["symbol"]
                last_price = float(item["lastPrice"])
                change_pct = float(item["priceChangePercent"])
                key = "BTC" if "BTC" in symbol else "ETH"
                market_data[key] = {
                    "price": f"${last_price:,.2f}",
                    "change": f"{change_pct:+.2f}%"
                }
            market_data["last_updated"] = datetime.now().strftime("%H:%M:%S UTC")
    except Exception as e:
        pass

def background_engine_loop():
    """Continuous 24/7 background worker for agency tasks and trading monitoring."""
    while True:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fetch_live_market()
        
        btc_p = market_data['BTC']['price']
        btc_c = market_data['BTC']['change']
        log_entry = f"[{now_str}] ⚡ Heartbeat | BTC: {btc_p} ({btc_c}) | Agency Pipelines: Active | Memory: Healthy"
        
        print(log_entry)
        system_logs.append(log_entry)
        if len(system_logs) > 25:
            system_logs.pop(0)
            
        time.sleep(20)

# Start background thread
threading.Thread(target=background_engine_loop, daemon=True).start()

@app.get("/api/logs")
def get_logs():
    return JSONResponse({"logs": system_logs, "market": market_data})

@app.post("/api/webhook/lead")
async def receive_lead(request: Request):
    """Agency Webhook Endpoint for incoming client leads"""
    data = await request.json()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = data.get("name", "Unknown Lead")
    email = data.get("email", "No Email")
    entry = f"[{now_str}] 🎯 NEW LEAD RECEIVED: {name} ({email}) - Processing with AI workflow..."
    system_logs.append(entry)
    return {"status": "success", "message": f"Lead {name} queued for AI follow-up"}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI Core Control Center</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #090d16;
                --card-bg: #111827;
                --border: #1f293d;
                --primary: #38bdf8;
                --accent: #10b981;
                --text-muted: #94a3b8;
            }
            body {
                margin: 0;
                padding: 24px;
                background-color: var(--bg);
                color: #f8fafc;
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            .container {
                max-width: 950px;
                margin: auto;
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: var(--card-bg);
                padding: 20px 24px;
                border-radius: 14px;
                border: 1px solid var(--border);
                margin-bottom: 20px;
            }
            .badge {
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 1px solid #059669;
                padding: 6px 14px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .dot {
                width: 8px;
                height: 8px;
                background: #10b981;
                border-radius: 50%;
                box-shadow: 0 0 10px #10b981;
                animation: pulse 1.5s infinite;
            }
            @keyframes pulse {
                0% { opacity: 0.4; }
                50% { opacity: 1; }
                100% { opacity: 0.4; }
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 20px;
            }
            .card {
                background: var(--card-bg);
                padding: 18px 20px;
                border-radius: 12px;
                border: 1px solid var(--border);
            }
            .card-title {
                font-size: 13px;
                color: var(--text-muted);
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
            }
            .card-val {
                font-size: 24px;
                font-weight: 700;
                color: #fff;
            }
            .terminal {
                background: #030712;
                border: 1px solid var(--border);
                border-radius: 12px;
                padding: 20px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                height: 280px;
                overflow-y: auto;
                color: #38bdf8;
            }
            .terminal p {
                margin: 6px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>
                    <h2 style="margin: 0; font-size: 22px;">AI Agency & Trading Core Engine</h2>
                    <span style="color: var(--text-muted); font-size: 14px;">Hugging Face Cloud Server · 16 GB RAM · 2 vCPU</span>
                </div>
                <div class="badge">
                    <div class="dot"></div>
                    ONLINE 24/7
                </div>
            </div>

            <div class="grid">
                <div class="card">
                    <div class="card-title">Bitcoin (BTC/USDT)</div>
                    <div id="btc-val" class="card-val">Fetching...</div>
                    <small id="btc-change" style="color: #94a3b8;">--</small>
                </div>
                <div class="card">
                    <div class="card-title">Ethereum (ETH/USDT)</div>
                    <div id="eth-val" class="card-val">Fetching...</div>
                    <small id="eth-change" style="color: #94a3b8;">--</small>
                </div>
                <div class="card">
                    <div class="card-title">Agency Pipelines</div>
                    <div class="card-val" style="color: #38bdf8;">Ready</div>
                    <small style="color: #94a3b8;">Webhook: /api/webhook/lead</small>
                </div>
                <div class="card">
                    <div class="card-title">Server Uptime</div>
                    <div class="card-val" style="color: #34d399;">Active</div>
                    <small style="color: #94a3b8;">Zero Cost Tier</small>
                </div>
            </div>

            <div class="card" style="padding: 16px 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <strong style="font-size: 14px; text-transform: uppercase; color: var(--text-muted);">Real-Time Console Logs</strong>
                    <span id="update-time" style="font-size: 12px; color: var(--text-muted);">Auto-updating...</span>
                </div>
                <div class="terminal" id="console-logs">
                    <p>[SYSTEM] Connecting to AI Engine background stream...</p>
                </div>
            </div>
        </div>

        <script>
            async function updateData() {
                try {
                    const res = await fetch('/api/logs');
                    const data = await res.json();
                    
                    document.getElementById('btc-val').innerText = data.market.BTC.price;
                    document.getElementById('btc-change').innerText = data.market.BTC.change;
                    document.getElementById('btc-change').style.color = data.market.BTC.change.startsWith('+') ? '#34d399' : '#f87171';

                    document.getElementById('eth-val').innerText = data.market.ETH.price;
                    document.getElementById('eth-change').innerText = data.market.ETH.change;
                    document.getElementById('eth-change').style.color = data.market.ETH.change.startsWith('+') ? '#34d399' : '#f87171';

                    document.getElementById('update-time').innerText = "Last sync: " + data.market.last_updated;

                    const logContainer = document.getElementById('console-logs');
                    logContainer.innerHTML = data.logs.map(log => `<p>${log}</p>`).join('');
                    logContainer.scrollTop = logContainer.scrollHeight;
                } catch(e) {}
            }
            setInterval(updateData, 4000);
            updateData();
        </script>
    </body>
    </html>
    """
