import time
import threading
from datetime import datetime
import requests
import gradio as gr

# Live State
market_data = {
    "BTC": "Fetching...",
    "ETH": "Fetching...",
    "last_updated": "Initializing..."
}
logs = []

def fetch_market():
    """Fetch live crypto ticker data from public Binance API"""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url, params={"symbols": '["BTCUSDT","ETHUSDT"]'}, timeout=5)
        if res.status_code == 200:
            for item in res.json():
                symbol = item["symbol"]
                price = float(item["lastPrice"])
                change = float(item["priceChangePercent"])
                if "BTC" in symbol:
                    market_data["BTC"] = f"${price:,.2f} ({change:+.2f}%)"
                elif "ETH" in symbol:
                    market_data["ETH"] = f"${price:,.2f} ({change:+.2f}%)"
            market_data["last_updated"] = datetime.now().strftime("%H:%M:%S UTC")
    except Exception as e:
        pass

def background_loop():
    """24/7 background worker for agency automation and market monitoring"""
    while True:
        fetch_market()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{now_str}] ⚡ Heartbeat | BTC: {market_data['BTC']} | ETH: {market_data['ETH']} | Cloud Status: Active"
        print(entry)
        logs.append(entry)
        if len(logs) > 30:
            logs.pop(0)
        time.sleep(15)

threading.Thread(target=background_loop, daemon=True).start()

def get_telemetry():
    log_text = "\n".join(reversed(logs)) if logs else "Starting up background monitoring engine..."
    return market_data["BTC"], market_data["ETH"], market_data["last_updated"], log_text

def simulate_agency_lead(name, email, service):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{now_str}] 🎯 NEW LEAD RECEIVED: {name} ({email}) | Service: {service} -> Sent to AI workflow!"
    logs.append(entry)
    return f"Success! Lead '{name}' queued for AI qualification & follow-up."

# Gradio Dashboard UI
with gr.Blocks(title="AI Agency & Trading Core", theme=gr.themes.Soft(primary_hue="sky")) as demo:
    gr.Markdown("# 🚀 AI Agency & Algorithmic Trading Core Engine\n**Cloud Server:** Hugging Face Spaces (16 GB RAM · 2 vCPU) | Status: **LIVE 24/7**")
    
    with gr.Row():
        btc_box = gr.Textbox(label="Bitcoin (BTC/USDT)", value="Loading...", interactive=False)
        eth_box = gr.Textbox(label="Ethereum (ETH/USDT)", value="Loading...", interactive=False)
        sync_box = gr.Textbox(label="Last Synced", value="Loading...", interactive=False)
    
    with gr.Tab("Live System Telemetry"):
        refresh_btn = gr.Button("🔄 Refresh Telemetry & Prices", variant="primary")
        console_box = gr.TextArea(label="Real-Time Engine Logs", value="Initializing...", lines=10, interactive=False)
        refresh_btn.click(get_telemetry, inputs=[], outputs=[btc_box, eth_box, sync_box, console_box])
        
    with gr.Tab("Agency Lead Webhook Simulator"):
        gr.Markdown("### Test Inbound Client Lead Processing")
        with gr.Row():
            lead_name = gr.Textbox(label="Client Name", placeholder="e.g. Acme Corp")
            lead_email = gr.Textbox(label="Client Email", placeholder="e.g. contact@acme.com")
            lead_service = gr.Dropdown(label="Service Required", choices=["Customer Support AI Chatbot", "n8n Workflow Automation", "AI Trading Algo"], value="Customer Support AI Chatbot")
        submit_btn = gr.Button("🚀 Submit Lead to AI Engine")
        result_box = gr.Textbox(label="AI Engine Response", interactive=False)
        submit_btn.click(simulate_agency_lead, inputs=[lead_name, lead_email, lead_service], outputs=[result_box])

    demo.load(get_telemetry, inputs=[], outputs=[btc_box, eth_box, sync_box, console_box])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
