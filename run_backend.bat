@echo off
title HealthBridge AI Backend Server
cd /d "%~dp0"
echo ========================================================
echo  HealthBridge AI - FastAPI Backend Server
echo  API Docs:  http://127.0.0.1:8000/docs
echo  Health:    http://127.0.0.1:8000/health
echo  App Home:  http://127.0.0.1:8000/
echo ========================================================

powershell -NoProfile -Command "$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; if ($conn) { Write-Host '[INFO] Port 8000 is already active and running!'; exit 0 } else { exit 1 }"
if %errorlevel% equ 0 (
    echo [INFO] FastAPI backend is already running on port 8000.
    echo Opening browser to http://127.0.0.1:8000/...
    start http://127.0.0.1:8000/
    timeout /t 3 >nul
    exit /b 0
)

echo Starting FastAPI Backend on http://127.0.0.1:8000...
echo [IMPORTANT] Keep this terminal window open while using the app!
echo ========================================================
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
