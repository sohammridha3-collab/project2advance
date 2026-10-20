@echo off
title HealthBridge AI - Public Cloudflare Tunnel
echo ======================================================================
echo           HealthBridge AI - Live Public Sharing Launcher
echo ======================================================================
echo.

:: Check if backend is active on port 8000
netstat -ano | findstr LISTENING | findstr :8000 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] FastAPI backend is not running yet. Starting backend now...
    start "" run_backend.bat
    timeout /t 3 /nobreak >nul
)

echo [INFO] Generating secure public link via Cloudflare Tunnel...
echo [INFO] Please wait a few seconds...
echo.
npx -y cloudflared tunnel --url http://127.0.0.1:8000
pause
