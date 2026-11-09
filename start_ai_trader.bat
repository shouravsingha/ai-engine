@echo off
title TradingAI 24/7 Exness Engine
echo ============================================================
echo   TradingAI 24/7 Autonomous Exness Engine & Cloud Bridge
echo   Account: #434353249 on Exness-MT5Trial7
echo   Cloud Web: https://ai-engine-6bpy.onrender.com/
echo ============================================================
echo.

echo [1/2] Launching MetaTrader 5 Terminal...
if exist "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe" (
    start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
)

echo Waiting for MT5 Terminal to connect to Exness broker...
timeout /t 5 /nobreak >nul

echo [2/2] Launching AI Engine, OrderFlow Matrix & Cloud Tunnel...
cd /d "C:\Users\HP\ai-engine"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
pause
