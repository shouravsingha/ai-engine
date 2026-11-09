import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.core.orchestrator import MasterOrchestrator

app = FastAPI(title="TradingAI · Real-Time Animated OrderFlow & 3D Office with AI Brain")
orchestrator = MasterOrchestrator()
cloud_command_queue = orchestrator.cloud_command_queue

from app.trading.exness_bridge import start_cloud_tunnel_daemon

@app.on_event("startup")
def startup_event():
    orchestrator.start_background_loop()
    start_cloud_tunnel_daemon(orchestrator.exness)

@app.post("/api/bridge/sync")
def bridge_sync(data: dict):
    """Tunnel endpoint on Render that ingests live MT5 state from local Windows host."""
    exness_data = data.get("exness", {})
    if exness_data:
        orchestrator.exness.apply_remote_sync(exness_data)
    commands = list(cloud_command_queue)
    cloud_command_queue.clear()
    return {"status": "ok", "commands": commands}

@app.get("/api/telemetry")
def get_telemetry():
    exness_status = orchestrator.exness.get_status()
    return JSONResponse({
        "account": orchestrator.account.get_summary(),
        "exness": exness_status,
        "market_matrix": orchestrator.multi_market_matrix,
        "orderflow": orchestrator.orderflow.get_order_flow_matrix(),
        "ai_brain": orchestrator.brain.get_status(),
        "agents": orchestrator.agents,
        "agent_messages": orchestrator.agent_messages,
        "open_trades": exness_status.get("open_positions", []),
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

class RiskModeInput(BaseModel):
    mode: str  # "conservative", "institutional", "aggressive"

class CloudConfigInput(BaseModel):
    token: str
    password: Optional[str] = ""
    server: Optional[str] = "Exness-MT5Trial7"

@app.post("/api/cloud/config")
def save_cloud_config(data: CloudConfigInput):
    orchestrator.exness.cloud_gateway.token = data.token.strip()
    if data.password:
        orchestrator.exness.cloud_gateway.password = data.password.strip()
    if data.server:
        orchestrator.exness.cloud_gateway.server = data.server.strip()
    
    sync_res = orchestrator.exness.cloud_gateway.sync_telemetry()
    configured = orchestrator.exness.cloud_gateway.is_configured()
    orchestrator.send_agent_message("Alex", "Chief Quant (PA_01)", f"☁️ 24/7 Cloud MetaAPI Gateway configured. Status: {'ACTIVE' if sync_res.get('status') == 'success' else 'STANDBY'}.")
    return {"status": "success", "configured": configured, "cloud_sync": sync_res}

@app.get("/api/cloud/status")
def get_cloud_status():
    gw = orchestrator.exness.cloud_gateway
    return {
        "configured": gw.is_configured(),
        "account_id": gw.account_id,
        "server": gw.server,
        "has_token": bool(gw.token),
        "has_password": bool(gw.password),
        "connected": gw.connected,
        "meta_account_id": gw.meta_account_id
    }

@app.post("/api/risk/mode")
def set_risk_mode(data: RiskModeInput):
    mode = data.mode.lower()
    if mode == "conservative":
        orchestrator.risk.risk_percent = 0.5
    elif mode == "aggressive":
        orchestrator.risk.risk_percent = 2.0
    else:
        orchestrator.risk.risk_percent = 1.0
    orchestrator.send_agent_message("AI Brain", "Neural Overseer", f"🧠 Risk calibration updated: {mode.upper()} mode ({orchestrator.risk.risk_percent}% risk ceiling per trade).")
    return {"status": "success", "mode": mode, "risk_percent": orchestrator.risk.risk_percent}

@app.post("/api/trade/panic_flat")
def panic_flat_all():
    if not (orchestrator.exness.live_terminal):
        cloud_command_queue.append({"action": "panic_flat"})
        closed_count = len(orchestrator.exness.open_positions)
        orchestrator.exness.open_positions = []
        orchestrator.account.open_trades.clear()
        orchestrator.send_agent_message("Marcus", "Risk Officer (PA_02)", f"🚨 EMERGENCY KILL SWITCH TRIGGERED: Dispatched flatten directive to live MT5 terminal.")
        return {"status": "queued_for_local_mt5", "closed_positions": closed_count}

    mt5_flat = orchestrator.exness.close_all_positions()
    closed_count = len(orchestrator.account.open_trades) + mt5_flat.get("total_closed", 0)
    orchestrator.account.open_trades.clear()
    orchestrator.send_agent_message("Marcus", "Risk Officer (PA_02)", f"🚨 EMERGENCY KILL SWITCH TRIGGERED: All {closed_count} positions flattened instantly on Exness MT5.")
    orchestrator.telegram.send_message("🚨 <b>EMERGENCY KILL SWITCH ACTIVATED</b>\nAll open positions flattened to preserve capital.")
    return {"status": "success", "closed_positions": closed_count, "mt5": mt5_flat}

@app.post("/api/trade/close/{ticket}")
def close_trade_by_ticket(ticket: int):
    if not (orchestrator.exness.live_terminal):
        cloud_command_queue.append({"action": "close", "ticket": ticket})
        orchestrator.exness.open_positions = [p for p in orchestrator.exness.open_positions if p.get("ticket") != ticket]
        orchestrator.send_agent_message("Leo", "Execution Trader (PA_14)", f"Cloud Close Directive sent for MT5 Ticket #{ticket}.")
        return {"status": "queued_for_local_mt5", "ticket": ticket}

    res = orchestrator.exness.close_position(ticket)
    orchestrator.send_agent_message("Leo", "Execution Trader (PA_14)", f"Manual Close for MT5 Ticket #{ticket}: {res.get('status', 'processed')}.")
    return res

@app.post("/api/trade/execute")
def direct_execute(data: dict):
    symbol = data.get("symbol", "XAUUSDm")
    side = data.get("side", "BUY")
    price = float(data.get("price", 2748.20))
    sl = price * 0.996 if side == "BUY" else price * 1.004
    tp = price * 1.012 if side == "BUY" else price * 0.988
    
    if not (orchestrator.exness.live_terminal):
        cloud_command_queue.append({
            "action": "execute",
            "symbol": symbol,
            "side": side,
            "volume": 0.01,
            "sl": sl,
            "tp": tp
        })
        plan = orchestrator.risk.evaluate_and_size_trade(orchestrator.exness.balance, side, price, sl, tp)
        order = orchestrator.account.open_trade(plan if plan else {"side": side, "entry_price": price, "stop_loss": sl, "take_profit": tp, "dollar_risk": 0.20, "units": 0.01}, symbol=symbol)
        orchestrator.send_agent_message("Leo", "Execution Trader (PA_14)", f"Cloud Trade Directive queued: {side} 0.01 {symbol} for live local MT5!")
        return {"status": "queued_for_local_mt5", "message": f"Queued {side} {symbol} for local MT5 terminal.", "order": order}

    # 1. Execute directly on physical Exness MT5 Terminal
    mt5_res = orchestrator.exness.execute_live_order(symbol, side, volume=0.01, sl=sl, tp=tp)
    
    # 2. Risk Evaluation & Internal Logging
    plan = orchestrator.risk.evaluate_and_size_trade(orchestrator.exness.balance, side, price, sl, tp)
    order = orchestrator.account.open_trade(plan if plan else {"side": side, "entry_price": price, "stop_loss": sl, "take_profit": tp, "dollar_risk": 0.20, "units": 0.01}, symbol=symbol)
    
    ticket_str = mt5_res.get("ticket", order["id"])
    orchestrator.send_agent_message("Leo", "Execution Trader (PA_14)", f"OrderFlow Live Execution: {side} 0.01 {symbol} on Exness MT5! Ticket #{ticket_str}.")
    orchestrator.telegram.send_trade_signal(order, asset=symbol)
    orchestrator.webhooks.broadcast_trade(order, asset=symbol)
    
    return {"status": "success", "order": order, "mt5_execution": mt5_res}

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OrderFlow by TradingAI · Institutional Currency & Commodities Matrix</title>
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Newsreader:ital,wght@1,500;1,600&display=swap" rel="stylesheet">
        <!-- Three.js + OrbitControls -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            :root {
                --of-bg: #eceef2;
                --of-card: #ffffff;
                --of-card-subtle: #f8fafc;
                --of-border: #e2e8f0;
                --of-border-strong: #cbd5e1;
                --of-text-dark: #0f172a;
                --of-text-muted: #64748b;
                --of-green: #10b981;
                --of-green-line: #059669;
                --of-green-bg: #ecfdf5;
                --of-red: #ef4444;
                --of-red-line: #dc2626;
                --of-red-bg: #fef2f2;
                --of-blue: #0284c7;
                --of-gold: #d97706;
                --of-gate-green: rgba(16, 185, 129, 0.18);
                --of-gate-red: rgba(239, 68, 68, 0.18);
                --of-shadow: 0 10px 40px rgba(0,0,0,0.12);
            }

            body.theme-dark {
                --of-bg: #07090e;
                --of-card: #0d121d;
                --of-card-subtle: #111726;
                --of-border: #1e293b;
                --of-border-strong: #334155;
                --of-text-dark: #f8fafc;
                --of-text-muted: #94a3b8;
                --of-green: #10b981;
                --of-green-line: #34d399;
                --of-green-bg: rgba(16, 185, 129, 0.15);
                --of-red: #ef4444;
                --of-red-line: #f87171;
                --of-red-bg: rgba(239, 68, 68, 0.15);
                --of-blue: #38bdf8;
                --of-gate-green: rgba(16, 185, 129, 0.25);
                --of-gate-red: rgba(239, 68, 68, 0.25);
                --of-shadow: 0 12px 50px rgba(0,0,0,0.6);
            }

            * { box-sizing: border-box; }
            body, html {
                margin: 0; padding: 0; width: 100%; height: 100%;
                background: #090d16; color: #fff;
                font-family: 'Plus Jakarta Sans', sans-serif;
            }

            /* Master Navigation Bar */
            .top-nav-bar {
                background: #0b0f19; border-bottom: 1px solid #1a2333;
                padding: 10px 24px; display: flex; justify-content: space-between; align-items: center;
                position: sticky; top: 0; z-index: 100;
            }
            .brand-flow { display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 15px; }
            .dot-flow { width: 9px; height: 9px; border-radius: 50%; background: #ef4444; animation: pulseRed 1.5s infinite; }
            @keyframes pulseRed { 0% { opacity: 0.3; } 50% { opacity: 1; } 100% { opacity: 0.3; } }

            .tab-switch { display: flex; gap: 8px; }
            .tab-btn {
                background: #131a29; border: 1px solid #1e293b; color: #94a3b8;
                padding: 7px 15px; border-radius: 8px; font-weight: 700; font-size: 12px;
                cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px;
            }
            .tab-btn.active, .tab-btn:hover { background: #0284c7; color: #fff; border-color: #0284c7; }

            /* View Containers */
            #view-orderflow { padding: 18px 24px 30px; max-width: 1680px; margin: auto; }
            #view-3d-floor { width: 100vw; height: calc(100vh - 58px); position: relative; display: none; }

            /* 100% IDENTICAL ORDERFLOW WINDOW (Matching new update.mp4) */
            .of-window {
                background: var(--of-card); color: var(--of-text-dark);
                border-radius: 18px; border: 1px solid var(--of-border-strong);
                box-shadow: var(--of-shadow); overflow: hidden; position: relative;
            }

            /* Mac-Style Header */
            .of-window-head {
                background: var(--of-card-subtle); border-bottom: 1px solid var(--of-border);
                padding: 10px 18px; display: flex; justify-content: space-between; align-items: center;
            }
            .of-mac-dots { display: flex; gap: 7px; align-items: center; }
            .mac-dot { width: 11px; height: 11px; border-radius: 50%; }

            .of-title-center {
                font-size: 15px; font-weight: 800; display: flex; align-items: center; gap: 6px;
            }
            .of-flow-serif { font-family: 'Newsreader', serif; font-style: italic; font-weight: 600; font-size: 18px; }

            .of-head-controls { display: flex; align-items: center; gap: 10px; }
            .of-pill-segment {
                background: var(--of-card); border: 1px solid var(--of-border);
                border-radius: 20px; padding: 2px 4px; display: flex; gap: 2px;
            }
            .of-seg-btn {
                background: transparent; border: none; font-size: 11.5px; font-weight: 700;
                padding: 4px 10px; border-radius: 16px; color: var(--of-text-muted); cursor: pointer;
            }
            .of-seg-btn.active { background: #0f172a; color: #fff; }
            body.theme-dark .of-seg-btn.active { background: #38bdf8; color: #000; }

            .of-theme-toggle {
                background: var(--of-card); border: 1px solid var(--of-border);
                border-radius: 50%; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;
                cursor: pointer; font-size: 13px; color: var(--of-text-muted);
            }

            /* Subheader Status Line */
            .of-subhead {
                background: var(--of-card-subtle); border-bottom: 1px solid var(--of-border);
                padding: 8px 18px; display: flex; justify-content: space-between; align-items: center;
                font-size: 11px; color: var(--of-text-muted); font-weight: 600;
            }

            /* Delta Imbalance Histogram Bar */
            .of-delta-bar {
                height: 28px; padding: 4px 20px 4px 140px; border-bottom: 1px solid var(--of-border);
                display: flex; align-items: flex-end; gap: 4px; background: var(--of-card);
            }
            .hist-col { width: 5px; border-radius: 1px; min-height: 3px; }

            /* MASTER BOARD GRID */
            .of-board-grid {
                display: grid;
                grid-template-columns: 130px minmax(460px, 1fr) 360px 100px 340px;
                min-height: 760px;
                position: relative;
            }

            /* 1. Left Percentage Axis */
            .of-axis-col {
                border-right: 1px solid var(--of-border); padding: 12px 6px;
                display: flex; flex-direction: column; justify-content: space-between;
                font-family: 'JetBrains Mono', monospace; font-size: 10.5px; color: var(--of-text-muted);
                position: relative; background: var(--of-card-subtle);
            }
            .axis-mark { display: flex; align-items: center; justify-content: space-between; height: 38px; }
            .sector-pill {
                padding: 2px 5px; border-radius: 4px; font-size: 9px; font-weight: 700;
                white-space: nowrap; font-family: 'Plus Jakarta Sans', sans-serif;
            }

            /* 2. River Sankey Flow Canvas Area */
            .of-river-col {
                position: relative; border-right: 1px solid var(--of-border);
                display: flex; flex-direction: column; overflow: hidden;
            }
            #sankey-river-canvas {
                width: 100%; height: 690px; display: block;
            }
            .of-timeline-bar {
                height: 40px; border-top: 1px solid var(--of-border);
                display: flex; justify-content: space-between; align-items: center;
                padding: 0 16px; font-family: 'JetBrains Mono'; font-size: 11px; color: var(--of-text-muted);
                background: var(--of-card-subtle);
            }
            .time-pill-active {
                background: #0f172a; color: #fff; padding: 2px 7px; border-radius: 4px; font-weight: 800;
            }
            body.theme-dark .time-pill-active { background: #38bdf8; color: #000; }

            /* 3. Fanning Grid of Currency/Stock Tiles */
            .of-tiles-col {
                border-right: 1px solid var(--of-border); padding: 12px 10px;
                display: flex; flex-direction: column; justify-content: space-between;
                background: var(--of-card); overflow-y: auto;
            }
            .tiles-cluster {
                display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;
            }
            .tile-unit {
                background: var(--of-card-subtle); border: 1px solid var(--of-border);
                border-radius: 7px; padding: 6px 7px; cursor: pointer; transition: all 0.15s;
                display: flex; flex-direction: column; gap: 2px;
            }
            .tile-unit:hover, .tile-unit.active {
                border-color: var(--of-blue); transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            }
            .tile-top { display: flex; justify-content: space-between; align-items: center; }
            .tile-code { font-size: 9.5px; font-weight: 800; color: var(--of-text-muted); }
            .tile-pct { font-size: 11px; font-weight: 800; font-family: 'JetBrains Mono'; }
            .tile-name { font-size: 10.5px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            .tile-buildup { font-size: 9px; color: var(--of-text-muted); }

            /* 4. Bid-Ask Volume Absorption Column */
            .of-histogram-col {
                border-right: 1px solid var(--of-border); padding: 16px 4px;
                display: flex; flex-direction: column; justify-content: space-around;
                background: var(--of-card-subtle);
            }
            .hist-dual-row {
                display: flex; flex-direction: column; align-items: center; gap: 4px;
            }
            .hist-dual-bars {
                display: flex; width: 100%; height: 10px; gap: 2px; justify-content: center;
            }
            .hist-bid-bar { background: var(--of-green); border-radius: 2px 0 0 2px; }
            .hist-ask-bar { background: var(--of-red); border-radius: 0 2px 2px 0; }
            .hist-price-badge {
                background: #0f172a; color: #fff; font-family: 'JetBrains Mono';
                font-size: 9.5px; font-weight: 700; padding: 2px 5px; border-radius: 3px;
            }
            body.theme-dark .hist-price-badge { background: #1e293b; color: #38bdf8; }

            /* 5. Right Focus Cards Column (Matching Frame 4) */
            .of-cards-col {
                padding: 12px 14px; background: var(--of-card-subtle);
                display: flex; flex-direction: column; gap: 10px; overflow-y: auto;
            }
            .focus-card {
                background: var(--of-card); border: 1px solid var(--of-border);
                border-radius: 12px; padding: 12px; transition: all 0.2s; cursor: pointer;
            }
            .focus-card:hover { border-color: var(--of-blue); }
            .focus-head { display: flex; justify-content: space-between; align-items: flex-start; }
            .focus-tag {
                font-size: 9.5px; font-weight: 800; padding: 2px 6px; border-radius: 4px;
            }
            .tag-bull { background: var(--of-green-bg); color: var(--of-green-line); }
            .tag-bear { background: var(--of-red-bg); color: var(--of-red-line); }
            .focus-price-row {
                display: flex; justify-content: space-between; align-items: baseline; margin: 4px 0 6px;
            }
            .focus-pct { font-size: 16px; font-weight: 800; font-family: 'JetBrains Mono'; }
            .focus-price { font-size: 12px; font-weight: 700; color: var(--of-text-muted); font-family: 'JetBrains Mono'; }
            .focus-chart-box { height: 44px; width: 100%; margin: 6px 0; }
            .focus-levels {
                display: flex; justify-content: space-between; font-size: 9.5px; color: var(--of-text-muted);
                border-top: 1px dashed var(--of-border); padding-top: 6px; margin-top: 4px;
            }

            /* FLOATING INSPECTION POPOVER CARD (Matching Frame 7 & 15) */
            #floating-popover {
                position: absolute; width: 380px; background: var(--of-card);
                border: 1px solid var(--of-border-strong); border-radius: 14px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.25); z-index: 50;
                padding: 16px; display: none; backdrop-filter: blur(12px);
            }
            body.theme-dark #floating-popover {
                background: rgba(13, 18, 29, 0.96); box-shadow: 0 20px 60px rgba(0,0,0,0.7);
            }
            .pop-head { display: flex; justify-content: space-between; align-items: flex-start; }
            .pop-badge {
                width: 32px; height: 32px; border-radius: 8px; background: var(--of-card-subtle);
                border: 1px solid var(--of-border); display: flex; align-items: center; justify-content: center;
                font-weight: 800; font-size: 13px; color: var(--of-blue);
            }
            .pop-close {
                background: transparent; border: none; font-size: 16px; cursor: pointer; color: var(--of-text-muted);
            }
            .pop-price-line {
                display: flex; align-items: baseline; gap: 8px; margin: 8px 0; font-family: 'JetBrains Mono';
            }
            .pop-chart-box {
                height: 100px; width: 100%; background: var(--of-card-subtle);
                border-radius: 8px; border: 1px solid var(--of-border); margin: 8px 0;
            }
            .pop-stats-grid {
                display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;
                font-size: 10.5px; margin: 10px 0; padding-bottom: 8px; border-bottom: 1px solid var(--of-border);
            }
            .pop-stats-grid small { color: var(--of-text-muted); display: block; font-size: 9px; }
            .pop-check-item {
                display: flex; align-items: center; gap: 6px; font-size: 11px; margin-bottom: 5px;
            }

            /* 3D Viewport Controls & AI Brain HUD */
            #canvas-3d-wrap { width: 100%; height: 100%; position: relative; }
            #webgl-canvas { width: 100%; height: 100%; display: block; }
            .brain-hud {
                position: absolute; top: 16px; left: 16px;
                background: rgba(11, 15, 27, 0.92); backdrop-filter: blur(12px);
                border: 1px solid rgba(236, 72, 153, 0.4); border-radius: 14px;
                padding: 12px 18px; z-index: 20; display: flex; align-items: center; gap: 14px;
            }
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

            /* ======================================================= */
            /* ULTRA-RESPONSIVE MOBILE & TABLET STYLING (iOS & Android) */
            /* ======================================================= */
            @media (max-width: 1024px) {
                #view-orderflow {
                    padding: 12px 14px 24px;
                }
                .of-board-grid {
                    grid-template-columns: 100px 1fr 300px;
                }
                .of-histogram-col, .of-cards-col {
                    display: none;
                }
            }

            @media (max-width: 768px) {
                body, html {
                    overflow-x: hidden;
                    width: 100%;
                }
                .top-nav-bar {
                    padding: 8px 10px;
                    flex-wrap: wrap;
                    gap: 8px;
                }
                .brand-flow {
                    font-size: 13.5px;
                    width: 100%;
                    justify-content: space-between;
                }
                .nav-badge-hide-mobile {
                    display: none !important;
                }
                .tab-switch {
                    width: 100%;
                    order: 3;
                    gap: 6px;
                }
                .tab-btn {
                    flex: 1;
                    justify-content: center;
                    padding: 8px 4px;
                    font-size: 11px;
                }
                .nav-risk-box {
                    width: 100%;
                    order: 4;
                    justify-content: space-between;
                }
                .nav-exness-card {
                    width: 100%;
                    order: 2;
                    padding: 8px 10px !important;
                    flex-wrap: wrap;
                    gap: 8px;
                    justify-content: space-between !important;
                }
                .nav-toggles-box {
                    width: 100%;
                    order: 5;
                    justify-content: space-between;
                    margin-top: 2px;
                }

                #view-orderflow {
                    padding: 6px 4px 16px;
                }
                .of-window {
                    border-radius: 12px;
                }
                .of-window-head {
                    padding: 8px 10px;
                    flex-wrap: wrap;
                    gap: 8px;
                }
                .of-head-controls {
                    width: 100%;
                    justify-content: space-between;
                }
                .of-pill-segment {
                    flex: 1;
                    justify-content: center;
                }
                .of-seg-btn {
                    flex: 1;
                    text-align: center;
                    padding: 4px 6px;
                    font-size: 10.5px;
                }

                /* Subhead Mobile Stack */
                .of-subhead {
                    flex-direction: column;
                    align-items: stretch;
                    gap: 8px;
                    padding: 10px;
                }
                .subhead-row-1 {
                    flex-wrap: wrap;
                    gap: 6px 10px;
                    font-size: 11px;
                }
                .subhead-row-2 {
                    flex-direction: column;
                    width: 100%;
                    gap: 6px;
                }
                #subhead-deal {
                    width: 100%;
                    justify-content: space-between;
                    box-sizing: border-box;
                    padding: 6px 10px;
                    font-size: 11px;
                }
                .quick-gold-btn {
                    width: 100%;
                    padding: 8px 12px;
                    font-size: 12px;
                    justify-content: center;
                    text-align: center;
                }

                .of-delta-bar {
                    padding: 4px 8px;
                    height: 24px;
                    overflow-x: auto;
                }

                /* Mobile Board Stack (River Canvas on top, Tiles below, Cards at bottom) */
                .of-board-grid {
                    display: flex;
                    flex-direction: column;
                    min-height: auto;
                    width: 100%;
                }

                /* Horizontal Sector Carousel on Mobile */
                .of-axis-col {
                    border-right: none;
                    border-bottom: 1px solid var(--of-border);
                    flex-direction: row;
                    overflow-x: auto;
                    padding: 8px 10px;
                    gap: 6px;
                    white-space: nowrap;
                    -webkit-overflow-scrolling: touch;
                }
                .axis-mark {
                    height: auto;
                    display: inline-flex;
                    border: none !important;
                }
                .axis-mark > span:first-child,
                .axis-mark > small {
                    display: none;
                }

                /* River Canvas area */
                .of-river-col {
                    border-right: none;
                    border-bottom: 1px solid var(--of-border);
                    width: 100%;
                }
                #sankey-river-canvas {
                    height: 330px !important;
                    width: 100% !important;
                }
                .of-timeline-bar {
                    height: 32px;
                    font-size: 9.5px;
                    padding: 0 8px;
                    overflow-x: auto;
                }

                /* Touch-Friendly Tile Clusters */
                .of-tiles-col {
                    border-right: none;
                    border-bottom: 1px solid var(--of-border);
                    padding: 12px 10px;
                    width: 100%;
                    box-sizing: border-box;
                }
                .tiles-cluster {
                    grid-template-columns: repeat(2, 1fr) !important;
                    gap: 8px;
                }
                .tile-unit {
                    padding: 8px 10px;
                    border-radius: 9px;
                }
                .tile-code {
                    font-size: 10px;
                }
                .tile-pct {
                    font-size: 12px;
                }
                .tile-name {
                    font-size: 11px;
                }

                /* Histogram / Absorption on mobile */
                .of-histogram-col {
                    display: flex;
                    flex-direction: row;
                    overflow-x: auto;
                    padding: 10px 8px;
                    border-right: none;
                    border-bottom: 1px solid var(--of-border);
                    gap: 12px;
                }
                .hist-dual-row {
                    min-width: 90px;
                }

                /* Focus Cards on mobile */
                .of-cards-col {
                    display: flex;
                    width: 100%;
                    padding: 12px 10px;
                    box-sizing: border-box;
                }
                .focus-card {
                    padding: 12px;
                }

                /* Mobile Native Bottom Drawer for Popover */
                #floating-popover {
                    position: fixed !important;
                    top: auto !important;
                    bottom: 0 !important;
                    left: 0 !important;
                    right: 0 !important;
                    width: 100% !important;
                    max-width: 100% !important;
                    border-radius: 20px 20px 0 0 !important;
                    border-left: none !important;
                    border-right: none !important;
                    border-bottom: none !important;
                    box-shadow: 0 -10px 40px rgba(0,0,0,0.6) !important;
                    max-height: 82vh;
                    overflow-y: auto;
                    padding: 16px 14px 28px !important;
                    z-index: 9999 !important;
                    transform: translateY(0);
                    animation: popoverSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
                }
                @keyframes popoverSlideUp {
                    from { transform: translateY(100%); }
                    to { transform: translateY(0); }
                }

                /* 3D Office on mobile */
                .brain-hud {
                    top: 8px;
                    left: 8px;
                    right: 8px;
                    padding: 8px 12px;
                    font-size: 11px;
                    flex-wrap: wrap;
                    gap: 8px;
                }
                .dock-3d {
                    bottom: 12px;
                    width: calc(100% - 24px);
                    box-sizing: border-box;
                    overflow-x: auto;
                    white-space: nowrap;
                    padding: 5px 8px;
                    gap: 4px;
                    -webkit-overflow-scrolling: touch;
                }
                .dock-btn {
                    padding: 5px 10px;
                    font-size: 10px;
                    flex-shrink: 0;
                }
            }
        </style>
    </head>
    <body class="theme-light">
        <!-- TOP APP BAR -->
        <header class="top-nav-bar">
            <div class="brand-flow">
                <span class="dot-flow"></span>
                <span>• OrderFlow <span class="of-flow-serif" style="color: #38bdf8;">by TradingAI</span></span>
                <span class="nav-badge-hide-mobile" style="background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">FOREX & COMMODITIES</span>
                <span class="nav-badge-hide-mobile" style="background: rgba(236,72,153,0.15); color: #ec4899; border: 1px solid rgba(236,72,153,0.3); padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700;">🧠 AI CENTRAL BRAIN ACTIVE</span>
            </div>

            <!-- View Switcher -->
            <div class="tab-switch">
                <button class="tab-btn active" onclick="switchView('orderflow')">🌊 OrderFlow Matrix (Exact Video Match)</button>
                <button class="tab-btn" onclick="switchView('3d')">🏢 3D Robot Floor (with AI Brain)</button>
            </div>

            <!-- Risk Mode & Emergency Kill Switch -->
            <div class="nav-risk-box" style="display: flex; align-items: center; gap: 8px;">
                <div style="background: #111726; border: 1px solid #1e293b; border-radius: 8px; padding: 4px 8px; display: flex; align-items: center; gap: 6px; font-size: 11px;">
                    <span style="color: #94a3b8; font-weight: 700;">Risk:</span>
                    <button onclick="setRisk('conservative')" id="risk-btn-cons" style="background: transparent; border: 1px solid #334155; color: #94a3b8; border-radius: 4px; padding: 2px 6px; font-size: 10px; cursor: pointer;">0.5%</button>
                    <button onclick="setRisk('institutional')" id="risk-btn-inst" style="background: #0284c7; border: 1px solid #0284c7; color: #fff; border-radius: 4px; padding: 2px 6px; font-size: 10px; cursor: pointer; font-weight: 800;">1.0%</button>
                    <button onclick="setRisk('aggressive')" id="risk-btn-aggr" style="background: transparent; border: 1px solid #334155; color: #94a3b8; border-radius: 4px; padding: 2px 6px; font-size: 10px; cursor: pointer;">2.0%</button>
                </div>
                <button onclick="panicFlatAll()" style="background: rgba(239,68,68,0.18); border: 1px solid #ef4444; color: #f87171; border-radius: 8px; padding: 6px 12px; font-weight: 800; font-size: 11px; cursor: pointer; display: flex; align-items: center; gap: 5px;">
                    🚨 PANIC FLAT ALL
                </button>
            </div>

            <!-- PROMINENT LIVE EXNESS MT5 ACCOUNT WIDGET (FRONT & CENTER) -->
            <div class="nav-exness-card" style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 5px 14px; display: flex; align-items: center; gap: 14px; font-family: 'JetBrains Mono'; font-size: 11.5px;">
                <span style="color: #10b981; font-weight: 800; display: flex; align-items: center; gap: 5px;">
                    <span style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; animation: pulseRed 1.5s infinite;"></span>
                    EXNESS MT5: #434353249
                </span>
                <span>Balance: <strong id="nav-exness-balance" style="color: #38bdf8; font-weight: 800; font-size: 13px;">$20.21 USD</strong></span>
                <span>Equity: <strong id="nav-exness-equity" style="color: #10b981; font-weight: 800;">$20.21</strong></span>
                <span>PnL: <strong id="nav-exness-pnl" style="color: #facc15;">+$0.00</strong></span>
                <span style="background: #0f172a; border: 1px solid #334155; padding: 2px 8px; border-radius: 4px; font-size: 10.5px;">
                    <span id="nav-open-count" style="color: #38bdf8; font-weight: 800;">0 Live Orders</span>
                </span>
            </div>

            <!-- Sound & Voice Toggles + 24/7 Cloud Bot + Exness Status -->
            <div class="nav-toggles-box" style="display: flex; align-items: center; gap: 8px; font-size: 12px;">
                <button onclick="openCloudModal()" style="background: rgba(14, 165, 233, 0.15); border: 1px solid #0ea5e9; color: #38bdf8; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; cursor: pointer; display: flex; align-items: center; gap: 4px;">
                    ☁️ 24/7 Cloud Bot
                </button>
                <button id="sound-btn" onclick="toggleSound()" style="background: #111726; border: 1px solid #1e293b; color: #38bdf8; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer;">
                    🔊 Audio: ON
                </button>
                <button id="voice-btn" onclick="toggleVoice()" style="background: #111726; border: 1px solid #1e293b; color: #ec4899; padding: 5px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; cursor: pointer;">
                    🗣️ Brain Voice: ON
                </button>
                <span style="color: #10b981; font-weight: 700; font-size: 11px;">● @SingAiTradebot</span>
            </div>
        </header>

        <!-- VIEW 1: 100% IDENTICAL ORDERFLOW MATRIX WINDOW (Matches new update.mp4) -->
        <div id="view-orderflow">
            <div class="of-window">
                <!-- Mac-Style Window Header -->
                <div class="of-window-head">
                    <div class="of-mac-dots">
                        <span class="mac-dot" style="background:#ff5f56;"></span>
                        <span class="mac-dot" style="background:#ffbd2e;"></span>
                        <span class="mac-dot" style="background:#27c93f;"></span>
                    </div>

                    <div class="of-title-center">
                        <span style="color: #ef4444; font-size: 10px;">●</span>
                        <span>Order<span class="of-flow-serif" style="color: #991b1b;">Flow</span></span>
                        <span style="font-size: 12px; font-weight: 400; color: var(--of-text-muted);">by TradingAI</span>
                    </div>

                    <div class="of-head-controls">
                        <div class="of-pill-segment">
                            <button class="of-seg-btn active" onclick="switchSegment(this, 'forex')">Forex Majors</button>
                            <button class="of-seg-btn" onclick="switchSegment(this, 'all')">All F&O / Crypto</button>
                        </div>
                        <div class="of-theme-toggle" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
                            <span id="theme-icon">🌙</span>
                        </div>
                    </div>
                </div>

                <!-- Subheader Status Line with Live Updating Exness Metrics -->
                <div class="of-subhead" id="subhead-exness-detail">
                    <div class="subhead-row-1" style="display: flex; align-items: center; gap: 8px;">
                        <span id="subhead-status-badge" style="color: #10b981; font-weight: 800;">● EXNESS MT5 LIVE (#434353249):</span>
                        <span>Balance: <strong style="color: var(--of-blue); font-size: 12px;" id="subhead-bal">$20.21 USD</strong></span>
                        <span>Equity: <strong id="subhead-eq" style="color: var(--of-green-line); font-size: 12px;">$20.21 USD</strong></span>
                        <span>PnL: <strong id="subhead-pnl" style="color: #10b981; font-size: 12px;">+$0.00 USD</strong></span>
                        <span style="color: var(--of-text-muted);">| 12 up · 8 flat · 10 down</span>
                    </div>
                    <div class="subhead-row-2" style="display: flex; align-items: center; gap: 8px;">
                        <span id="subhead-deal" style="background: var(--of-card); border: 1px solid var(--of-border); padding: 3px 8px; border-radius: 6px; font-family: 'JetBrains Mono'; font-size: 10.5px; color: var(--of-blue); display: flex; align-items: center; gap: 6px;">
                            <span style="color:var(--of-text-muted);">0 Active MT5 Positions · Scanning OrderFlow</span>
                        </span>
                        <button class="quick-gold-btn" onclick="quickOpenTrade('XAUUSDm', 'BUY')" style="background: rgba(245,158,11,0.15); border: 1px solid rgba(245,158,11,0.4); color: #f59e0b; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 10px; cursor: pointer;">
                            ⚡ Quick Buy Gold
                        </button>
                    </div>
                </div>

                <!-- Delta Imbalance Histogram Bar -->
                <div class="of-delta-bar" id="delta-hist-container"></div>

                <!-- MASTER BOARD GRID -->
                <div class="of-board-grid">
                    <!-- 1. LEFT PERCENTAGE AXIS & SECTOR PILLS -->
                    <div class="of-axis-col">
                        <div class="axis-mark"><span>+8%</span></div>
                        <div class="axis-mark"><span>+5%</span><span class="sector-pill" style="background:var(--of-green-bg); color:var(--of-green-line);">Gold +2.04%</span></div>
                        <div class="axis-mark"><span>+3%</span><span class="sector-pill" style="background:var(--of-green-bg); color:var(--of-green-line);">Crypto +2.18%</span></div>
                        <div class="axis-mark"><span>+2%</span><span class="sector-pill" style="background:var(--of-green-bg); color:var(--of-green-line);">EUR +0.84%</span></div>
                        <div class="axis-mark"><span>+1%</span><span class="sector-pill" style="background:var(--of-green-bg); color:var(--of-green-line);">GBP +0.62%</span></div>
                        <div class="axis-mark"><span>+0.5%</span></div>
                        <div class="axis-mark"><span>+0.1%</span></div>
                        <div class="axis-mark" style="font-weight: 800; color: var(--of-text-dark); border-top: 1px dashed var(--of-border); border-bottom: 1px dashed var(--of-border);"><span>0%</span><small>DXY 0.00%</small></div>
                        <div class="axis-mark"><span>-0.1%</span></div>
                        <div class="axis-mark"><span>-0.5%</span><span class="sector-pill" style="background:var(--of-red-bg); color:var(--of-red-line);">USD -0.55%</span></div>
                        <div class="axis-mark"><span>-1%</span><span class="sector-pill" style="background:var(--of-red-bg); color:var(--of-red-line);">CAD -0.74%</span></div>
                        <div class="axis-mark"><span>-2%</span><span class="sector-pill" style="background:var(--of-red-bg); color:var(--of-red-line);">JPY -1.12%</span></div>
                        <div class="axis-mark"><span>-3%</span><span class="sector-pill" style="background:var(--of-red-bg); color:var(--of-red-line);">Gas -2.45%</span></div>
                        <div class="axis-mark"><span>-5%</span></div>
                        <div class="axis-mark"><span>-8%</span></div>
                    </div>

                    <!-- 2. SANKEY STREAM RIVER CANVAS (WITH DUAL GATES) -->
                    <div class="of-river-col">
                        <canvas id="sankey-river-canvas"></canvas>
                        <div class="of-timeline-bar">
                            <span>09:15</span>
                            <span>10:00</span>
                            <span>11:00</span>
                            <span>12:00</span>
                            <span>13:00</span>
                            <span class="time-pill-active">13:31 (SCRUB)</span>
                            <span>14:00</span>
                            <span>15:30</span>
                        </div>
                    </div>

                    <!-- 3. FANNING OUT GRID OF ASSET TILES -->
                    <div class="of-tiles-col">
                        <!-- Upper Bullish Cluster -->
                        <div>
                            <div style="font-size: 10px; font-weight: 800; color: var(--of-green-line); margin-bottom: 6px; text-transform: uppercase;">
                                Bullish Convergence (Inflows)
                            </div>
                            <div class="tiles-cluster" id="bullish-tiles-box"></div>
                        </div>

                        <!-- Lower Bearish Cluster -->
                        <div style="margin-top: 14px;">
                            <div style="font-size: 10px; font-weight: 800; color: var(--of-red-line); margin-bottom: 6px; text-transform: uppercase;">
                                Bearish Convergence (Outflows)
                            </div>
                            <div class="tiles-cluster" id="bearish-tiles-box"></div>
                        </div>
                    </div>

                    <!-- 4. VOLUME ABSORPTION BID-ASK HISTOGRAMS -->
                    <div class="of-histogram-col" id="absorption-hist-box"></div>

                    <!-- 5. RIGHT FOCUS CARDS (SIEMENS, SENSEX, HINDALCO, BRITANNIA MATCH) -->
                    <div class="of-cards-col" id="focus-cards-box"></div>
                </div>
            </div>

            <!-- FLOATING INSPECTION POPOVER CARD (Matching Frame 7 & 15) -->
            <div id="floating-popover">
                <div class="pop-head">
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <div class="pop-badge" id="pop-code">XAU</div>
                        <div>
                            <strong id="pop-title" style="font-size: 14px;">XAUUSD (Gold Spot)</strong>
                            <div id="pop-subtitle" style="font-size: 10.5px; color: var(--of-text-muted);">Precious Metals · Commodities · Institutional Flow</div>
                        </div>
                    </div>
                    <button class="pop-close" onclick="closePopover()">✕</button>
                </div>

                <div class="pop-price-line">
                    <span id="pop-price" style="font-size: 20px; font-weight: 800; color: var(--of-green-line);">$2,748.20</span>
                    <span id="pop-chg" style="font-size: 12px; font-weight: 700; color: var(--of-green-line);">+2.04% (+54.80)</span>
                </div>

                <canvas id="pop-candle-chart" class="pop-chart-box"></canvas>

                <div class="pop-stats-grid">
                    <div><small>Rank</small><strong id="pop-rank">#1 of 30</strong></div>
                    <div><small>Build-up</small><strong id="pop-buildup" style="color: var(--of-green-line);">Long build-up</strong></div>
                    <div><small>Conviction</small><strong id="pop-conviction" style="color: var(--of-blue);">●●●●● 5/5</strong></div>
                    <div><small>Support</small><span id="pop-support">S1 2735.00</span></div>
                    <div><small>Zone</small><span id="pop-zone">2742 - 2748</span></div>
                    <div><small>Resistance</small><span id="pop-resistance">R1 2765.00</span></div>
                </div>

                <div style="font-size: 11px; font-weight: 800; margin: 6px 0 4px;">Why it ranks here:</div>
                <div class="pop-check-item"><span style="color: var(--of-green); font-weight: bold;">✓</span> <span>Positions opened with the move (Institutional Delta expansion)</span></div>
                <div class="pop-check-item"><span style="color: var(--of-green); font-weight: bold;">✓</span> <span>The last 1H/4H candle agrees with Higher High structure</span></div>
                <div class="pop-check-item"><span style="color: var(--of-green); font-weight: bold;">✓</span> <span>US Dollar index (DXY) leaning opposite direction (USD Weakness)</span></div>
                <div class="pop-check-item"><span style="color: var(--of-green); font-weight: bold;">✓</span> <span>Mitigated 0.618 Fibonacci Golden Pocket in Discount Zone</span></div>

                <button onclick="executePopoverPair()" style="width: 100%; margin-top: 10px; padding: 10px; border-radius: 8px; border: none; background: #0284c7; color: #fff; font-weight: 800; font-size: 12px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px;">
                    ⚡ Execute Order on Exness MT5 (#434353249)
                </button>
            </div>
        </div>

        <!-- 24/7 CLOUD AUTONOMOUS TRADING SETTINGS MODAL -->
        <div id="cloud-modal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); backdrop-filter:blur(8px); z-index:10000; align-items:center; justify-content:center; padding:16px;">
            <div style="background:var(--of-card); border:1px solid var(--of-border-strong); border-radius:16px; max-width:500px; width:100%; padding:24px; box-shadow:0 25px 60px rgba(0,0,0,0.5); font-family:'Plus Jakarta Sans',sans-serif; color:var(--of-text-dark);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:22px;">☁️</span>
                        <div>
                            <h3 style="margin:0; font-size:16px; font-weight:800;">24/7 Cloud MT5 Autonomous Engine</h3>
                            <small style="color:var(--of-text-muted); font-size:11px;">Runs on Render even when your laptop is turned OFF</small>
                        </div>
                    </div>
                    <button onclick="closeCloudModal()" style="background:transparent; border:none; font-size:18px; cursor:pointer; color:var(--of-text-muted);">✕</button>
                </div>

                <div id="cloud-status-badge" style="background:rgba(14,165,233,0.1); border:1px solid rgba(14,165,233,0.3); border-radius:10px; padding:10px 14px; margin-bottom:16px; font-size:12px; display:flex; justify-content:space-between; align-items:center;">
                    <span>Cloud Gateway Status:</span>
                    <strong id="cloud-status-text" style="color:#38bdf8;">Checking...</strong>
                </div>

                <div style="font-size:11.5px; color:var(--of-text-muted); margin-bottom:14px; line-height:1.5;">
                    Connect your Exness account to MetaAPI Cloud Gateway. Once connected, Render executes trades directly on the broker's servers 24 hours a day, 7 days a week.
                </div>

                <div style="margin-bottom:12px;">
                    <label style="display:block; font-size:11px; font-weight:700; margin-bottom:4px; color:var(--of-text-muted);">EXNESS MT5 LOGIN ID</label>
                    <input id="cloud-input-login" type="text" value="434353249" readonly style="width:100%; background:var(--of-card-subtle); border:1px solid var(--of-border); border-radius:8px; padding:8px 10px; font-family:'JetBrains Mono'; font-size:12px; color:var(--of-text-dark);">
                </div>

                <div style="margin-bottom:12px;">
                    <label style="display:block; font-size:11px; font-weight:700; margin-bottom:4px; color:var(--of-text-muted);">EXNESS SERVER</label>
                    <input id="cloud-input-server" type="text" value="Exness-MT5Trial7" style="width:100%; background:var(--of-card-subtle); border:1px solid var(--of-border); border-radius:8px; padding:8px 10px; font-family:'JetBrains Mono'; font-size:12px; color:var(--of-text-dark);">
                </div>

                <div style="margin-bottom:12px;">
                    <div style="display:flex; justify-content:space-between; align-items:baseline;">
                        <label style="font-size:11px; font-weight:700; margin-bottom:4px; color:var(--of-text-muted);">METAAPI FREE CLOUD TOKEN</label>
                        <a href="https://app.metaapi.cloud/token" target="_blank" style="font-size:10px; color:#38bdf8; text-decoration:none; font-weight:700;">Get Free Token ↗</a>
                    </div>
                    <input id="cloud-input-token" type="password" placeholder="Paste your MetaAPI token here" style="width:100%; background:var(--of-card-subtle); border:1px solid var(--of-border); border-radius:8px; padding:8px 10px; font-family:'JetBrains Mono'; font-size:12px; color:var(--of-text-dark);">
                </div>

                <div style="margin-bottom:16px;">
                    <label style="display:block; font-size:11px; font-weight:700; margin-bottom:4px; color:var(--of-text-muted);">EXNESS TRADING PASSWORD</label>
                    <input id="cloud-input-pass" type="password" placeholder="Exness MT5 account password" style="width:100%; background:var(--of-card-subtle); border:1px solid var(--of-border); border-radius:8px; padding:8px 10px; font-family:'JetBrains Mono'; font-size:12px; color:var(--of-text-dark);">
                </div>

                <div style="display:flex; gap:10px;">
                    <button onclick="saveCloudConfig()" id="cloud-save-btn" style="flex:1; background:linear-gradient(135deg, #0284c7, #0369a1); border:none; color:#fff; border-radius:10px; padding:10px; font-weight:800; font-size:12.5px; cursor:pointer;">
                        ⚡ Save & Arm 24/7 Cloud Trading
                    </button>
                    <button onclick="closeCloudModal()" style="background:var(--of-card-subtle); border:1px solid var(--of-border); color:var(--of-text-muted); border-radius:10px; padding:10px 14px; font-size:12px; cursor:pointer;">
                        Cancel
                    </button>
                </div>
            </div>
        </div>

        <!-- VIEW 2: 3D ROBOT OFFICE WITH AI CENTRAL NEURAL BRAIN -->
        <div id="view-3d-floor">
            <div id="canvas-3d-wrap">
                <div class="brain-hud">
                    <div style="width: 14px; height: 14px; border-radius: 50%; background: #ec4899; box-shadow: 0 0 15px #ec4899;"></div>
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
            let currentDataset = null;
            let selectedPairData = null;
            let isDark = false;
            let soundEnabled = true;
            let voiceEnabled = true;
            let audioCtx = null;

            function initAudio() {
                if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            }

            function playAudioFx(type) {
                if (!soundEnabled) return;
                try {
                    initAudio();
                    const osc = audioCtx.createOscillator();
                    const gain = audioCtx.createGain();
                    osc.connect(gain);
                    gain.connect(audioCtx.destination);

                    if (type === 'trade') {
                        osc.type = 'triangle';
                        osc.frequency.setValueAtTime(587.33, audioCtx.currentTime);
                        osc.frequency.exponentialRampToValueAtTime(880.00, audioCtx.currentTime + 0.12);
                        gain.gain.setValueAtTime(0.2, audioCtx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.35);
                        osc.start(); osc.stop(audioCtx.currentTime + 0.35);
                    } else if (type === 'alert') {
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(1046.50, audioCtx.currentTime);
                        gain.gain.setValueAtTime(0.18, audioCtx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.45);
                        osc.start(); osc.stop(audioCtx.currentTime + 0.45);
                    } else if (type === 'brain') {
                        osc.type = 'sine';
                        osc.frequency.setValueAtTime(440, audioCtx.currentTime);
                        osc.frequency.linearRampToValueAtTime(659.25, audioCtx.currentTime + 0.2);
                        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
                        gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.4);
                        osc.start(); osc.stop(audioCtx.currentTime + 0.4);
                    }
                } catch(e) {}
            }

            function toggleSound() {
                soundEnabled = !soundEnabled;
                document.getElementById('sound-btn').innerText = soundEnabled ? '🔊 Audio: ON' : '🔇 Audio: OFF';
                document.getElementById('sound-btn').style.color = soundEnabled ? '#38bdf8' : '#64748b';
            }

            function toggleVoice() {
                voiceEnabled = !voiceEnabled;
                document.getElementById('voice-btn').innerText = voiceEnabled ? '🗣️ Brain Voice: ON' : '🤐 Brain Voice: OFF';
                document.getElementById('voice-btn').style.color = voiceEnabled ? '#ec4899' : '#64748b';
            }

            function speakBrainMessage(msg) {
                if (!voiceEnabled || !window.speechSynthesis) return;
                try {
                    window.speechSynthesis.cancel();
                    const utter = new SpeechSynthesisUtterance(msg);
                    utter.rate = 1.05; utter.pitch = 1.1;
                    window.speechSynthesis.speak(utter);
                } catch(e) {}
            }

            function toggleTheme() {
                isDark = !isDark;
                document.body.className = isDark ? 'theme-dark' : 'theme-light';
                document.getElementById('theme-icon').innerText = isDark ? '☀️' : '🌙';
                drawSankeyRiver();
            }

            function switchSegment(btn, seg) {
                document.querySelectorAll('.of-seg-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                playAudioFx('alert');
            }

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

            async function setRisk(mode) {
                const res = await fetch('/api/risk/mode', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ mode: mode })
                });
                const d = await res.json();
                ['cons', 'inst', 'aggr'].forEach(m => {
                    const btn = document.getElementById(`risk-btn-${m}`);
                    btn.style.background = 'transparent'; btn.style.color = '#94a3b8'; btn.style.fontWeight = 'normal';
                });
                const activeId = mode === 'conservative' ? 'cons' : (mode === 'aggressive' ? 'aggr' : 'inst');
                const activeBtn = document.getElementById(`risk-btn-${activeId}`);
                activeBtn.style.background = '#0284c7'; activeBtn.style.color = '#fff'; activeBtn.style.fontWeight = '800';
                playAudioFx('brain');
                speakBrainMessage(`Risk ceiling locked at ${d.risk_percent} percent.`);
            }

            async function panicFlatAll() {
                if (!confirm("EMERGENCY KILL SWITCH: Flatten all open positions immediately?")) return;
                const res = await fetch('/api/trade/panic_flat', { method: 'POST' });
                const d = await res.json();
                playAudioFx('trade');
                speakBrainMessage("Emergency kill switch activated. All positions flattened.");
                alert(`All ${d.closed_positions} positions flattened to cash! Capital preserved.`);
            }

            // RENDER DELTA HISTOGRAM
            function renderDeltaHistogram() {
                const cont = document.getElementById('delta-hist-container');
                let html = '';
                for (let i = 0; i < 48; i++) {
                    const isBull = (i > 10 && i < 24) || (i > 32);
                    const h = 4 + Math.floor(Math.sin(i * 0.4) * 8 + 8);
                    const bg = isBull ? 'var(--of-green)' : 'var(--of-red)';
                    html += `<div class="hist-col" style="height:${h}px; background:${bg};"></div>`;
                }
                cont.innerHTML = html;
            }

            // CONTINUOUS 60 FPS ANIMATED FLUID SANKEY RIVER WITH MOVING PARTICLES & GATES
            let riverParticles = [];
            let wavePhase = 0;
            let riverAnimId = null;

            function initRiverParticles() {
                riverParticles = [];
                for (let i = 0; i < 90; i++) {
                    const isBull = Math.random() < 0.58;
                    riverParticles.push({
                        isBull: isBull,
                        progress: Math.random(),
                        speed: 0.0035 + Math.random() * 0.005,
                        width: 2 + Math.random() * 3,
                        yJitter: (Math.random() - 0.5) * 26,
                        pulse: Math.random() * Math.PI * 2
                    });
                }
            }

            function animateRiverLoop() {
                wavePhase += 0.035;
                drawSankeyRiver(wavePhase);
                riverAnimId = requestAnimationFrame(animateRiverLoop);
            }

            function drawSankeyRiver(phase = 0) {
                const canvas = document.getElementById('sankey-river-canvas');
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                if (canvas.width !== canvas.clientWidth * window.devicePixelRatio) {
                    canvas.width = canvas.clientWidth * window.devicePixelRatio;
                    canvas.height = canvas.clientHeight * window.devicePixelRatio;
                }

                const W = canvas.width;
                const H = canvas.height;

                ctx.clearRect(0, 0, W, H);

                // Zero baseline
                const zeroY = H * 0.52;
                ctx.strokeStyle = isDark ? '#1e293b' : '#e2e8f0';
                ctx.lineWidth = 1.5;
                ctx.setLineDash([4, 4]);
                ctx.beginPath();
                ctx.moveTo(0, zeroY);
                ctx.lineTo(W, zeroY);
                ctx.stroke();
                ctx.setLineDash([]);

                // Benchmark DXY line with wave modulation
                ctx.strokeStyle = isDark ? '#475569' : '#94a3b8';
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(20, zeroY + 10);
                const dxyWave = Math.sin(phase * 1.5) * 4;
                ctx.bezierCurveTo(W * 0.3, zeroY + 25 + dxyWave, W * 0.6, zeroY + 15 - dxyWave, W - 20, zeroY + 28);
                ctx.stroke();

                // DUAL CONVERGENCE TUNNELS / GATES (WITH GLOWING PULSE)
                const gatePulse = Math.sin(phase * 2) * 0.08;

                // 1. Upper Green Gate (Bullish Funnel)
                const gUpperX = W * 0.72;
                const gUpperY = H * 0.14;
                const gW = W * 0.12;
                const gH = H * 0.18;

                ctx.fillStyle = isDark ? `rgba(16, 185, 129, ${0.22 + gatePulse})` : `rgba(16, 185, 129, ${0.12 + gatePulse})`;
                ctx.fillRect(gUpperX, gUpperY, gW, gH);
                ctx.strokeStyle = '#10b981';
                ctx.lineWidth = 2.5 + Math.sin(phase * 2.5) * 0.8;
                ctx.strokeRect(gUpperX, gUpperY, gW, gH);

                ctx.fillStyle = '#10b981';
                ctx.font = `bold ${10 * window.devicePixelRatio}px sans-serif`;
                ctx.fillText('▲ BULLISH GATE', gUpperX + 8, gUpperY - 8);

                // 2. Lower Red Gate (Bearish Funnel)
                const gLowerX = W * 0.72;
                const gLowerY = H * 0.68;

                ctx.fillStyle = isDark ? `rgba(239, 68, 68, ${0.22 + gatePulse})` : `rgba(239, 68, 68, ${0.12 + gatePulse})`;
                ctx.fillRect(gLowerX, gLowerY, gW, gH);
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 2.5 + Math.sin(phase * 2.5 + 1) * 0.8;
                ctx.strokeRect(gLowerX, gLowerY, gW, gH);

                ctx.fillStyle = '#ef4444';
                ctx.fillText('▼ BEARISH GATE', gLowerX + 8, gLowerY + gH + 16 * window.devicePixelRatio);

                // Draw Multiple Continuous River Streams (Animated Wave Physics)
                const streamCount = 28;
                for (let i = 0; i < streamCount; i++) {
                    const isBull = i < 15;
                    const waveMod = Math.sin(phase + i * 0.35) * 7;
                    const startY = zeroY + (Math.sin(i) * 35) + waveMod * 0.4;
                    const targetGateY = isBull ? (gUpperY + (i % 5) * (gH / 5) + 8) : (gLowerY + (i % 5) * (gH / 5) + 8);
                    const endY = isBull ? (targetGateY - 10 + Math.sin(i * 2 + phase) * 16) : (targetGateY + 10 + Math.sin(i * 2 + phase) * 16);

                    ctx.strokeStyle = isBull 
                        ? (isDark ? 'rgba(16, 185, 129, 0.28)' : 'rgba(16, 185, 129, 0.38)')
                        : (isDark ? 'rgba(239, 68, 68, 0.28)' : 'rgba(239, 68, 68, 0.38)');
                    ctx.lineWidth = 1.6;

                    ctx.beginPath();
                    ctx.moveTo(10, startY);
                    ctx.bezierCurveTo(
                        W * 0.25, startY + (isBull ? -40 : 40) + waveMod,
                        W * 0.5, targetGateY + (isBull ? 25 : -25) - waveMod,
                        gUpperX, targetGateY
                    );
                    ctx.lineTo(gUpperX + gW, targetGateY);
                    ctx.bezierCurveTo(
                        gUpperX + gW + W * 0.05, targetGateY,
                        W * 0.92, endY,
                        W - 5, endY
                    );
                    ctx.stroke();
                }

                // 🌊 LIVE FLOWING PARTICLES ALONG THE RIVER PATHS
                riverParticles.forEach(p => {
                    p.progress += p.speed;
                    if (p.progress > 1) p.progress = 0;

                    const t = p.progress;
                    const isBull = p.isBull;
                    const startY = zeroY + p.yJitter;
                    const targetGateY = isBull ? (gUpperY + gH * 0.45 + p.yJitter * 0.6) : (gLowerY + gH * 0.45 + p.yJitter * 0.6);
                    const endY = isBull ? (gUpperY + p.yJitter * 0.8) : (gLowerY + gH + p.yJitter * 0.8);

                    let px, py;
                    if (t < 0.68) {
                        // Phase 1: From left (09:15) to Gate entrance
                        const subT = t / 0.68;
                        const cp1X = W * 0.25, cp1Y = startY + (isBull ? -40 : 40);
                        const cp2X = W * 0.5, cp2Y = targetGateY + (isBull ? 25 : -25);
                        px = (1 - subT)**3 * 10 + 3 * (1 - subT)**2 * subT * cp1X + 3 * (1 - subT) * subT**2 * cp2X + subT**3 * gUpperX;
                        py = (1 - subT)**3 * startY + 3 * (1 - subT)**2 * subT * cp1Y + 3 * (1 - subT) * subT**2 * cp2Y + subT**3 * targetGateY;
                    } else if (t < 0.80) {
                        // Phase 2: Squeezing through the Gate
                        const subT = (t - 0.68) / 0.12;
                        px = gUpperX + subT * gW;
                        py = targetGateY;
                    } else {
                        // Phase 3: Fanning out into the tiles
                        const subT = (t - 0.80) / 0.20;
                        const cp1X = gUpperX + gW + W * 0.05, cp1Y = targetGateY;
                        const cp2X = W * 0.92, cp2Y = endY;
                        px = (1 - subT)**3 * (gUpperX + gW) + 3 * (1 - subT)**2 * subT * cp1X + 3 * (1 - subT) * subT**2 * cp2X + subT**3 * (W - 5);
                        py = (1 - subT)**3 * targetGateY + 3 * (1 - subT)**2 * subT * cp1Y + 3 * (1 - subT) * subT**2 * cp2Y + subT**3 * endY;
                    }

                    ctx.fillStyle = isBull ? '#10b981' : '#ef4444';
                    ctx.shadowColor = isBull ? '#10b981' : '#ef4444';
                    ctx.shadowBlur = isDark ? 8 : 4;
                    ctx.beginPath();
                    ctx.arc(px, py, p.width * window.devicePixelRatio * 0.65, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.shadowBlur = 0;
                });

                // Highlight Selected Asset Neon Line (e.g. Gold XAUUSD)
                const selIsBull = selectedPairData ? selectedPairData.direction === 'BULLISH' : true;
                ctx.strokeStyle = selIsBull ? '#10b981' : '#ef4444';
                ctx.lineWidth = 4 * window.devicePixelRatio;
                ctx.shadowColor = selIsBull ? '#10b981' : '#ef4444';
                ctx.shadowBlur = isDark ? 16 : 8;

                const hStartY = zeroY + 12;
                const hGateY = selIsBull ? gUpperY + gH * 0.45 : gLowerY + gH * 0.45;
                const hEndY = selIsBull ? gUpperY + 10 : gLowerY + 25;

                ctx.beginPath();
                ctx.moveTo(15, hStartY);
                ctx.bezierCurveTo(W * 0.25, hStartY - 60, W * 0.45, hGateY - 20, gUpperX, hGateY);
                ctx.lineTo(gUpperX + gW, hGateY);
                ctx.bezierCurveTo(gUpperX + gW + W * 0.04, hGateY, W * 0.92, hEndY, W - 10, hEndY);
                ctx.stroke();

                // Bright traveling pulse on selected asset
                const pulseT = (phase * 0.4) % 1;
                let hpx = W * pulseT;
                let hpy = zeroY + (selIsBull ? -1 : 1) * Math.sin(pulseT * Math.PI) * (H * 0.3);
                ctx.fillStyle = '#ffffff';
                ctx.shadowColor = '#ffffff';
                ctx.shadowBlur = 15;
                ctx.beginPath();
                ctx.arc(hpx, hpy, 5 * window.devicePixelRatio, 0, Math.PI * 2);
                ctx.fill();

                ctx.shadowBlur = 0; // reset
            }

            // RENDER TILES, HISTOGRAMS & FOCUS CARDS
            function renderBoardData(data) {
                currentDataset = data;

                // 1. Bullish Tiles
                const bBox = document.getElementById('bullish-tiles-box');
                bBox.innerHTML = (data.bullish_pairs || []).map(p => `
                    <div class="tile-unit ${selectedPairData && selectedPairData.symbol === p.symbol ? 'active' : ''}" onclick='openInspection(${JSON.stringify(p)}, this)'>
                        <div class="tile-top">
                            <span class="tile-code">${p.code || 'FX'}</span>
                            <span class="tile-pct" style="color:var(--of-green-line);">+${p.chg.toFixed(2)}%</span>
                        </div>
                        <div class="tile-name">${p.symbol}</div>
                        <div class="tile-buildup">${p.buildup}</div>
                    </div>
                `).join('');

                // 2. Bearish Tiles
                const dBox = document.getElementById('bearish-tiles-box');
                dBox.innerHTML = (data.bearish_pairs || []).map(p => `
                    <div class="tile-unit ${selectedPairData && selectedPairData.symbol === p.symbol ? 'active' : ''}" onclick='openInspection(${JSON.stringify(p)}, this)'>
                        <div class="tile-top">
                            <span class="tile-code">${p.code || 'FX'}</span>
                            <span class="tile-pct" style="color:var(--of-red-line);">${p.chg.toFixed(2)}%</span>
                        </div>
                        <div class="tile-name">${p.symbol}</div>
                        <div class="tile-buildup">${p.buildup}</div>
                    </div>
                `).join('');

                // 3. Bid-Ask Absorption Histograms
                const hBox = document.getElementById('absorption-hist-box');
                const samplePairs = [
                    data.bullish_pairs[0] || {symbol: 'XAUUSD', price: 2748.20},
                    data.bullish_pairs[1] || {symbol: 'BTCUSD', price: 67850.00},
                    data.bearish_pairs[0] || {symbol: 'USDJPY', price: 151.80},
                    data.bearish_pairs[1] || {symbol: 'USDCAD', price: 1.3820}
                ];
                hBox.innerHTML = samplePairs.map((sp, idx) => `
                    <div class="hist-dual-row">
                        <div class="hist-dual-bars">
                            <div class="hist-bid-bar" style="width: ${50 + idx * 8}%;"></div>
                            <div class="hist-ask-bar" style="width: ${50 - idx * 8}%;"></div>
                        </div>
                        <span class="hist-price-badge">${sp.price > 100 ? sp.price.toLocaleString('en-US', {minimumFractionDigits:2}) : sp.price.toFixed(4)}</span>
                    </div>
                `).join('');

                // 4. Focus Cards (Frame 4 Match)
                const fBox = document.getElementById('focus-cards-box');
                const focusItems = [
                    ...(data.bullish_pairs ? data.bullish_pairs.slice(0, 2) : []),
                    ...(data.bearish_pairs ? data.bearish_pairs.slice(0, 2) : [])
                ];
                fBox.innerHTML = focusItems.map(p => {
                    const isBull = p.direction === 'BULLISH';
                    return `
                    <div class="focus-card" onclick='openInspection(${JSON.stringify(p)})'>
                        <div class="focus-head">
                            <div>
                                <strong style="font-size: 13px;">${p.symbol}</strong>
                                <div style="font-size: 10px; color: var(--of-text-muted);">${p.type}</div>
                            </div>
                            <span class="focus-tag ${isBull ? 'tag-bull' : 'tag-bear'}">
                                ${p.direction} (${p.conviction})
                            </span>
                        </div>
                        <div class="focus-price-row">
                            <span class="focus-pct" style="color: ${isBull ? 'var(--of-green-line)' : 'var(--of-red-line)'};">
                                ${p.chg >= 0 ? '+' : ''}${p.chg.toFixed(2)}%
                            </span>
                            <span class="focus-price">$${p.price.toLocaleString('en-US', {minimumFractionDigits: 2})}</span>
                        </div>
                        <!-- Mini Trend Chart SVG with Dotted Levels -->
                        <div class="focus-chart-box">
                            <svg width="100%" height="100%" viewBox="0 0 280 44">
                                <line x1="0" y1="8" x2="280" y2="8" stroke="${isBull ? '#10b981' : '#ef4444'}" stroke-dasharray="3,3" opacity="0.4" />
                                <text x="240" y="7" fill="var(--of-text-muted)" font-size="8">R1 ${p.resistance.split(' ')[0]}</text>
                                <line x1="0" y1="36" x2="280" y2="36" stroke="${isBull ? '#10b981' : '#ef4444'}" stroke-dasharray="3,3" opacity="0.4" />
                                <text x="240" y="42" fill="var(--of-text-muted)" font-size="8">S1 ${p.support.split(' ')[0]}</text>
                                <path d="${isBull ? 'M 10 38 Q 80 34, 140 22 T 260 10' : 'M 10 10 Q 80 16, 140 26 T 260 38'}" fill="none" stroke="${isBull ? '#10b981' : '#ef4444'}" stroke-width="2" />
                            </svg>
                        </div>
                        <div class="focus-levels">
                            <span>SUPPORT: <b>${p.support.split(' ')[0]}</b></span>
                            <span>ZONE: <b>${p.zone}</b></span>
                            <span>RESISTANCE: <b>${p.resistance.split(' ')[0]}</b></span>
                        </div>
                    </div>
                `}).join('');
            }

            // OPEN INSPECTION POPOVER (Matching Frame 7 & 15)
            function openInspection(pair, elem) {
                selectedPairData = pair;
                const pop = document.getElementById('floating-popover');
                pop.style.display = 'block';

                document.getElementById('pop-code').innerText = pair.code || 'FX';
                document.getElementById('pop-title').innerText = pair.symbol;
                document.getElementById('pop-subtitle').innerText = `${pair.name || pair.type} · Institutional OrderFlow`;
                document.getElementById('pop-price').innerText = '$' + pair.price.toLocaleString('en-US', {minimumFractionDigits: 2});
                document.getElementById('pop-price').style.color = pair.direction === 'BULLISH' ? 'var(--of-green-line)' : 'var(--of-red-line)';
                document.getElementById('pop-chg').innerText = `${pair.chg >= 0 ? '+' : ''}${pair.chg.toFixed(2)}% (${pair.abs_chg ? (pair.abs_chg > 0 ? '+' : '') + pair.abs_chg : ''})`;
                document.getElementById('pop-chg').style.color = pair.direction === 'BULLISH' ? 'var(--of-green-line)' : 'var(--of-red-line)';

                document.getElementById('pop-buildup').innerText = pair.buildup;
                document.getElementById('pop-buildup').style.color = pair.direction === 'BULLISH' ? 'var(--of-green-line)' : 'var(--of-red-line)';
                document.getElementById('pop-conviction').innerText = `●●●●● ${pair.conviction}`;
                document.getElementById('pop-support').innerText = pair.support;
                document.getElementById('pop-zone').innerText = pair.zone;
                document.getElementById('pop-resistance').innerText = pair.resistance;

                // Position popover
                if (window.innerWidth <= 768) {
                    pop.style.left = '0px';
                    pop.style.top = 'auto';
                    pop.style.bottom = '0px';
                    pop.style.width = '100%';
                } else {
                    pop.style.bottom = 'auto';
                    pop.style.width = '380px';
                    if (elem) {
                        const rect = elem.getBoundingClientRect();
                        const winRect = document.querySelector('.of-window').getBoundingClientRect();
                        pop.style.left = `${Math.max(20, Math.min(rect.left - winRect.left - 390, winRect.width - 410))}px`;
                        pop.style.top = `${Math.max(rect.top - winRect.top - 80, 70)}px`;
                    } else {
                        pop.style.left = '48%';
                        pop.style.top = '120px';
                    }
                }

                drawPopoverCandles(pair);
                drawSankeyRiver(); // re-draw river highlighting selected pair
                playAudioFx('alert');
            }

            function closePopover() {
                document.getElementById('floating-popover').style.display = 'none';
            }

            function openCloudModal() {
                const modal = document.getElementById('cloud-modal');
                if (modal) {
                    modal.style.display = 'flex';
                    loadCloudStatus();
                }
            }

            function closeCloudModal() {
                const modal = document.getElementById('cloud-modal');
                if (modal) modal.style.display = 'none';
            }

            async function loadCloudStatus() {
                try {
                    const res = await fetch('/api/cloud/status');
                    if (res.ok) {
                        const d = await res.json();
                        const txt = document.getElementById('cloud-status-text');
                        if (txt) {
                            if (d.configured) {
                                txt.innerText = d.connected ? '● CONNECTED (24/7 ACTIVE)' : '● CONFIGURED (PROVISIONING)';
                                txt.style.color = '#10b981';
                            } else {
                                txt.innerText = '○ NOT CONFIGURED (STANDBY)';
                                txt.style.color = '#f59e0b';
                            }
                        }
                    }
                } catch(e) {}
            }

            async function saveCloudConfig() {
                const token = document.getElementById('cloud-input-token').value.trim();
                const pass = document.getElementById('cloud-input-pass').value.trim();
                const server = document.getElementById('cloud-input-server').value.trim();
                const btn = document.getElementById('cloud-save-btn');

                if (!token) {
                    alert('Please enter your MetaAPI Cloud Token (free from app.metaapi.cloud).');
                    return;
                }

                btn.innerText = 'Connecting to MetaAPI Cloud...';
                btn.disabled = true;

                try {
                    const res = await fetch('/api/cloud/config', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ token: token, password: pass, server: server })
                    });
                    const d = await res.json();
                    if (d.status === 'success') {
                        speakBrainMessage('24/7 Cloud MetaAPI Gateway armed successfully.');
                        alert('✅ 24/7 Cloud Gateway Armed! The bot can now trade continuously on Render even when your laptop is turned off.');
                        closeCloudModal();
                    } else {
                        alert('Could not configure cloud gateway: ' + JSON.stringify(d));
                    }
                } catch(e) {
                    alert('Error saving cloud config: ' + e);
                } finally {
                    btn.innerText = '⚡ Save & Arm 24/7 Cloud Trading';
                    btn.disabled = false;
                }
            }

            function drawPopoverCandles(pair) {
                const cv = document.getElementById('pop-candle-chart');
                if (!cv) return;
                const ctx = cv.getContext('2d');
                cv.width = cv.clientWidth * window.devicePixelRatio;
                cv.height = cv.clientHeight * window.devicePixelRatio;

                ctx.fillStyle = isDark ? '#111726' : '#f8fafc';
                ctx.fillRect(0, 0, cv.width, cv.height);

                // Dotted levels
                ctx.strokeStyle = isDark ? '#334155' : '#cbd5e1';
                ctx.setLineDash([3, 3]);
                ctx.beginPath();
                ctx.moveTo(0, cv.height * 0.25); ctx.lineTo(cv.width, cv.height * 0.25);
                ctx.moveTo(0, cv.height * 0.75); ctx.lineTo(cv.width, cv.height * 0.75);
                ctx.stroke();
                ctx.setLineDash([]);

                // Step / Candlestick line
                const count = 18;
                const w = cv.width / count;
                const isBull = pair.direction === 'BULLISH';
                ctx.strokeStyle = isBull ? '#10b981' : '#ef4444';
                ctx.fillStyle = isBull ? '#10b981' : '#ef4444';
                ctx.lineWidth = 2;

                ctx.beginPath();
                for (let i = 0; i < count; i++) {
                    const progress = i / count;
                    const y = isBull 
                        ? cv.height * 0.8 - (progress * cv.height * 0.6) + Math.sin(i) * 6
                        : cv.height * 0.2 + (progress * cv.height * 0.6) + Math.sin(i) * 6;
                    if (i === 0) ctx.moveTo(i * w, y);
                    else ctx.lineTo(i * w, y);
                    ctx.fillRect(i * w - 1.5, y - 1.5, 3, 3);
                }
                ctx.stroke();
            }

            async function quickOpenTrade(symbol, side) {
                playAudioFx('trade');
                const price = symbol.includes('XAU') ? 2748.20 : 1.1156;
                const res = await fetch('/api/trade/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ symbol: symbol, side: side, price: price })
                });
                const d = await res.json();
                speakBrainMessage(`Order placed. ${side} ${symbol} on Exness MT5.`);
                syncData();
            }

            async function closeTrade(ticket) {
                if (!confirm(`Close position #${ticket} on Exness MT5?`)) return;
                playAudioFx('trade');
                const res = await fetch('/api/trade/close/' + ticket, { method: 'POST' });
                const d = await res.json();
                speakBrainMessage("Position closed on Exness MT5.");
                syncData();
            }

            async function executePopoverPair() {
                if (!selectedPairData) return;
                const side = selectedPairData.direction === 'BULLISH' ? 'BUY' : 'SELL';
                playAudioFx('trade');
                const res = await fetch('/api/trade/execute', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        symbol: selectedPairData.symbol.includes('Gold') ? 'XAUUSDm' : selectedPairData.symbol,
                        side: side,
                        price: selectedPairData.price
                    })
                });
                const d = await res.json();
                speakBrainMessage(`Order placed. ${side} ${selectedPairData.symbol} on Exness MT5.`);
                syncData();
            }

            async function syncData() {
                try {
                    const res = await fetch('/api/telemetry');
                    const d = await res.json();
                    if (d.orderflow) {
                        renderBoardData(d.orderflow);
                        if (!selectedPairData && d.orderflow.bullish_pairs && d.orderflow.bullish_pairs.length > 0) {
                            selectedPairData = d.orderflow.bullish_pairs[0];
                        }
                    }

                    // UPDATE PROMINENT LIVE EXNESS MT5 METRICS & OPEN POSITIONS TABLE
                    if (d.exness) {
                        const bal = Number(d.exness.balance).toFixed(2);
                        const eq = Number(d.exness.equity).toFixed(2);
                        const pnl = Number(d.exness.floating_pnl || 0.0).toFixed(2);
                        const openCount = d.exness.open_positions ? d.exness.open_positions.length : 0;
                        const freeMargin = (Number(d.exness.equity) - (openCount * 0.56)).toFixed(2);

                        // Top Nav Bar Widget
                        const navBal = document.getElementById('nav-exness-balance');
                        if (navBal) navBal.innerText = `$${bal} USD`;
                        const navEq = document.getElementById('nav-exness-equity');
                        if (navEq) navEq.innerText = `$${eq}`;
                        const navPnl = document.getElementById('nav-exness-pnl');
                        if (navPnl) {
                            navPnl.innerText = `${pnl >= 0 ? '+' : ''}$${pnl}`;
                            navPnl.style.color = pnl >= 0 ? '#10b981' : '#ef4444';
                        }
                        const navCount = document.getElementById('nav-open-count');
                        if (navCount) {
                            navCount.innerText = `${openCount} Live Order${openCount === 1 ? '' : 's'}`;
                        }

                        // Window Subheader
                        const subBal = document.getElementById('subhead-bal');
                        if (subBal) subBal.innerText = `$${bal} USD`;
                        const subEq = document.getElementById('subhead-eq');
                        if (subEq) subEq.innerText = `$${eq} USD`;

                        const subPnl = document.getElementById('subhead-pnl');
                        if (subPnl) {
                            subPnl.innerText = `${pnl >= 0 ? '+' : ''}$${pnl} USD`;
                            subPnl.style.color = pnl >= 0 ? '#10b981' : '#ef4444';
                        }

                        // Subhead Live Connection Indicator
                        const statusBadge = document.getElementById('subhead-status-badge');
                        if (statusBadge) {
                            if (d.exness.live_terminal) {
                                statusBadge.innerHTML = `<span style="color: #10b981; font-weight: 800;">● EXNESS MT5 LIVE (#${d.exness.account_id}):</span>`;
                            } else {
                                statusBadge.innerHTML = `<span style="color: #ef4444; font-weight: 800;" title="Ensure start_ai_trader.bat is running on your laptop">● MT5 OFFLINE / LAPTOP CLOSED:</span>`;
                            }
                        }

                        const subDeal = document.getElementById('subhead-deal');
                        if (subDeal) {
                            if (openCount === 0) {
                                subDeal.innerHTML = `<span style="color:var(--of-text-muted);">0 Active MT5 Positions · Scanning OrderFlow</span>`;
                            } else if (openCount === 1 && d.exness.open_positions[0]) {
                                const pos = d.exness.open_positions[0];
                                subDeal.innerHTML = `Active: <b style="color:var(--of-blue);">${pos.symbol}</b> ${pos.side} ${pos.volume} (<span style="color:${pos.profit >= 0 ? '#10b981' : '#ef4444'}; font-weight:800;">${pos.profit >= 0 ? '+' : ''}$${pos.profit}</span>) <button onclick="closeTrade(${pos.ticket})" style="background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #ef4444; border-radius: 4px; padding: 1px 5px; font-size: 9px; cursor: pointer; margin-left: 4px;">✕ Close</button>`;
                            } else {
                                // Multiple positions active: render all neatly
                                const posListHtml = d.exness.open_positions.map(pos => 
                                    `<span><b style="color:var(--of-blue);">${pos.symbol}</b> ${pos.side} ${pos.volume} (<span style="color:${pos.profit >= 0 ? '#10b981' : '#ef4444'}; font-weight:800;">${pos.profit >= 0 ? '+' : ''}$${pos.profit}</span>) <button onclick="closeTrade(${pos.ticket})" style="background: rgba(239,68,68,0.15); border: 1px solid #ef4444; color: #ef4444; border-radius: 4px; padding: 0 4px; font-size: 8.5px; cursor: pointer;">✕</button></span>`
                                ).join(' <span style="color:var(--of-border-strong);">|</span> ');
                                subDeal.innerHTML = `<span style="font-weight:800; color:#38bdf8; margin-right:4px;">[${openCount} Trades]:</span> ${posListHtml}`;
                            }
                        }

                        // Exness Terminal Panel Cards
                        const pBal = document.getElementById('panel-exness-balance');
                        if (pBal) pBal.innerText = `$${bal} USD`;
                        const pEq = document.getElementById('panel-exness-equity');
                        if (pEq) pEq.innerText = `$${eq} USD`;
                        const pPnl = document.getElementById('panel-exness-pnl');
                        if (pPnl) {
                            pPnl.innerText = `${pnl >= 0 ? '+' : ''}$${pnl} USD`;
                            pPnl.style.color = pnl >= 0 ? 'var(--of-green-line)' : 'var(--of-red-line)';
                        }
                        const pMargin = document.getElementById('panel-exness-margin');
                        if (pMargin) pMargin.innerText = `$${freeMargin} USD`;
                        const pCount = document.getElementById('panel-open-count');
                        if (pCount) pCount.innerText = openCount;

                        // Exness Open Positions Table Rows
                        const tbody = document.getElementById('open-positions-tbody');
                        if (tbody) {
                            const positions = d.exness.open_positions || [];
                            if (positions.length === 0) {
                                tbody.innerHTML = `
                                    <tr>
                                        <td colspan="10" style="padding: 24px; text-align: center; color: var(--of-text-muted); font-style: italic;">
                                            No active open positions on Exness MT5 right now. Click "Quick Buy Gold" or execute from OrderFlow above.
                                        </td>
                                    </tr>
                                `;
                            } else {
                                tbody.innerHTML = positions.map(pos => {
                                    const isBuy = pos.side === 'BUY';
                                    const isProfitable = pos.profit >= 0;
                                    return `
                                        <tr style="border-bottom: 1px solid var(--of-border); transition: background 0.15s;">
                                            <td style="padding: 10px; font-weight: 800; color: var(--of-blue);">#${pos.ticket}</td>
                                            <td style="padding: 10px; font-weight: 800; color: var(--of-text-dark);">${pos.symbol}</td>
                                            <td style="padding: 10px;">
                                                <span style="background: ${isBuy ? 'var(--of-green-bg)' : 'var(--of-red-bg)'}; color: ${isBuy ? 'var(--of-green-line)' : 'var(--of-red-line)'}; padding: 3px 8px; border-radius: 4px; font-weight: 800; font-size: 10.5px;">
                                                    ${pos.side}
                                                </span>
                                            </td>
                                            <td style="padding: 10px; font-weight: 700;">${Number(pos.volume).toFixed(2)} Lot</td>
                                            <td style="padding: 10px;">${pos.open_price}</td>
                                            <td style="padding: 10px; font-weight: 800; color: ${isProfitable ? 'var(--of-green-line)' : 'var(--of-red-line)'};">${pos.current_price}</td>
                                            <td style="padding: 10px; color: var(--of-text-muted);">${pos.sl || 'None'}</td>
                                            <td style="padding: 10px; color: var(--of-text-muted);">${pos.tp || 'None'}</td>
                                            <td style="padding: 10px; font-weight: 800; font-size: 13.5px; color: ${isProfitable ? 'var(--of-green-line)' : 'var(--of-red-line)'};">
                                                ${isProfitable ? '+' : ''}$${Number(pos.profit).toFixed(2)}
                                            </td>
                                            <td style="padding: 10px; text-align: right;">
                                                <button onclick="closeTrade(${pos.ticket})" style="background: rgba(239,68,68,0.12); border: 1px solid #ef4444; color: #f87171; border-radius: 6px; padding: 4px 10px; font-size: 10.5px; font-weight: 800; cursor: pointer;">
                                                    ✕ Close MT5
                                                </button>
                                            </td>
                                        </tr>
                                    `;
                                }).join('');
                            }
                        }
                    }
                } catch(e) {}
            }

            // 3D Engine with AI Central Neural Brain & 7 Seated Robot Employees
            let scene, camera, renderer, controls;
            let brainCoreMesh, neuralRings = [], laserBeams = [];

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

                // 7 Robot Pods with swivel chairs, monitors, and overhead floating badges
                const robotConfigs = [
                    {x: -12, z: -6, color: 0xfacc15, tag: "PA_01 Alex (Chief Quant)"},
                    {x: -4,  z: -6, color: 0x3b82f6, tag: "LUC_3 David (Fibonacci)"},
                    {x: 4,   z: -6, color: 0x22c55e, tag: "PA_02 Marcus (Risk Officer)"},
                    {x: 12,  z: -6, color: 0x06b6d4, tag: "PA_14 Leo (Exness MT5)"},
                    {x: -8,  z: 8,  color: 0xf97316, tag: "Conta_1612 Sophia (Brand Director)"},
                    {x: 0,   z: 8,  color: 0xa855f7, tag: "PA_07 Mia (Viral Copy)"},
                    {x: 8,   z: 8,  color: 0x818cf8, tag: "PA_18 Noah (Video Master)"}
                ];

                robotConfigs.forEach(cfg => {
                    create3DPod(cfg.x, cfg.z, cfg.color, cfg.tag);
                    createNeuralLaserBeam(0, 7.5, 0, cfg.x, 2.0, cfg.z, cfg.color);
                });

                // Giant LED Wall showing equity curve at North Wall
                const ledWall = new THREE.Mesh(new THREE.BoxGeometry(28, 8, 0.2), new THREE.MeshStandardMaterial({ color: 0x0284c7, emissive: 0x0369a1, emissiveIntensity: 0.4 }));
                ledWall.position.set(0, 6, -21.8);
                scene.add(ledWall);

                function loop() {
                    requestAnimationFrame(loop);
                    controls.update();

                    if (brainCoreMesh) {
                        brainCoreMesh.rotation.y += 0.015;
                        brainCoreMesh.rotation.x += 0.008;
                        neuralRings.forEach((r, idx) => {
                            r.rotation.x += 0.02 * (idx + 1);
                            r.rotation.y += 0.015 * (idx + 1);
                        });
                    }

                    const t = Date.now() * 0.003;
                    laserBeams.forEach((beam, idx) => {
                        beam.material.opacity = 0.25 + Math.sin(t + idx) * 0.2;
                    });

                    renderer.render(scene, camera);
                }
                loop();
            }

            function createCentralAIBrain(x, y, z) {
                const brainGroup = new THREE.Group();
                brainGroup.position.set(x, y, z);

                const coreGeo = new THREE.IcosahedronGeometry(1.8, 2);
                const coreMat = new THREE.MeshStandardMaterial({
                    color: 0xec4899,
                    emissive: 0xec4899,
                    emissiveIntensity: 0.8,
                    wireframe: true
                });
                brainCoreMesh = new THREE.Mesh(coreGeo, coreMat);
                brainGroup.add(brainCoreMesh);

                const innerGeo = new THREE.SphereGeometry(1.1, 16, 16);
                const innerMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
                const inner = new THREE.Mesh(innerGeo, innerMat);
                brainGroup.add(inner);

                for (let i = 0; i < 3; i++) {
                    const ringGeo = new THREE.TorusGeometry(2.6 + (i * 0.4), 0.04, 8, 48);
                    const ringMat = new THREE.MeshBasicMaterial({ color: i === 0 ? 0x38bdf8 : (i === 1 ? 0x10b981 : 0xec4899) });
                    const ring = new THREE.Mesh(ringGeo, ringMat);
                    neuralRings.push(ring);
                    brainGroup.add(ring);
                }

                const beamGeo = new THREE.CylinderGeometry(0.1, 1.8, 7.5, 16);
                const beamMat = new THREE.MeshBasicMaterial({ color: 0xec4899, transparent: true, opacity: 0.25 });
                const beam = new THREE.Mesh(beamGeo, beamMat);
                beam.position.y = -3.75;
                brainGroup.add(beam);

                scene.add(brainGroup);
            }

            function createNeuralLaserBeam(x1, y1, z1, x2, y2, z2, colorHex) {
                const points = [new THREE.Vector3(x1, y1, z1), new THREE.Vector3(x2, y2, z2)];
                const geo = new THREE.BufferGeometry().setFromPoints(points);
                const mat = new THREE.LineBasicMaterial({ color: colorHex, transparent: true, opacity: 0.35, linewidth: 2 });
                const line = new THREE.Line(geo, mat);
                laserBeams.push(line);
                scene.add(line);
            }

            function create3DPod(x, z, c, tag) {
                const g = new THREE.Group(); g.position.set(x, 0, z);

                const d = new THREE.Mesh(new THREE.BoxGeometry(4.8, 1.3, 2.4), new THREE.MeshStandardMaterial({ color: 0x111726 }));
                d.position.y = 1.3; g.add(d);

                for(let m = -1; m <= 1; m += 2) {
                    const scr = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.0, 0.08), new THREE.MeshBasicMaterial({ color: 0x0284c7 }));
                    scr.position.set(m*1.0, 2.4, -0.6); g.add(scr);
                }

                const seat = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.2, 1.2), new THREE.MeshStandardMaterial({ color: 0x334155 }));
                seat.position.set(0, 1.0, 0.8); g.add(seat);
                const back = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.2, 0.2), new THREE.MeshStandardMaterial({ color: 0x334155 }));
                back.position.set(0, 1.6, 1.3); g.add(back);

                const botBody = new THREE.Mesh(new THREE.BoxGeometry(0.9, 1.0, 0.8), new THREE.MeshStandardMaterial({ color: c }));
                botBody.position.set(0, 1.6, 0.8); g.add(botBody);

                const botHead = new THREE.Mesh(new THREE.BoxGeometry(0.65, 0.55, 0.6), new THREE.MeshStandardMaterial({ color: 0xffffff }));
                botHead.position.set(0, 2.4, 0.8); g.add(botHead);

                const tagCanvas = document.createElement('canvas');
                tagCanvas.width = 256; tagCanvas.height = 64;
                const tctx = tagCanvas.getContext('2d');
                tctx.fillStyle = '#111726';
                tctx.fillRect(0, 0, 256, 64);
                tctx.fillStyle = '#38bdf8';
                tctx.font = 'bold 22px sans-serif';
                tctx.fillText(tag.split(' ')[0], 20, 40);

                const texture = new THREE.CanvasTexture(tagCanvas);
                const spriteMat = new THREE.SpriteMaterial({ map: texture });
                const sprite = new THREE.Sprite(spriteMat);
                sprite.position.set(0, 3.4, 0.8);
                sprite.scale.set(3, 0.75, 1);
                g.add(sprite);

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
                renderDeltaHistogram();
                initRiverParticles();
                animateRiverLoop();
                syncData();
                setInterval(syncData, 2000);
            };

            window.onresize = () => {
                const canvas = document.getElementById('sankey-river-canvas');
                if (canvas) {
                    canvas.width = canvas.clientWidth * window.devicePixelRatio;
                    canvas.height = canvas.clientHeight * window.devicePixelRatio;
                }
                if (typeof renderer !== 'undefined' && renderer && typeof camera !== 'undefined' && camera) {
                    const wrap = document.getElementById('canvas-3d-wrap');
                    if (wrap && wrap.clientWidth > 0 && wrap.clientHeight > 0) {
                        camera.aspect = wrap.clientWidth / wrap.clientHeight;
                        camera.updateProjectionMatrix();
                        renderer.setSize(wrap.clientWidth, wrap.clientHeight);
                    }
                }
            };
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
