@echo off
title HealthBridge AI - Install Permanent Auto-Start Service
cd /d "%~dp0"

echo ========================================================
echo   HealthBridge AI - Permanent Auto-Start Configuration
echo ========================================================
echo.
echo Installing background auto-start services:
echo  1. Windows Startup Shortcut (Background Logon Service)
echo  2. Windows Scheduled Task (Automatic Startup Daemon)
echo  3. Desktop 1-Click Shortcut ("HealthBridge AI")
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_autostart.ps1"

echo.
echo ========================================================
echo  Checking Backend Status on http://127.0.0.1:8000/ ...
echo ========================================================
timeout /t 2 >nul

powershell -NoProfile -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 3; Write-Host '[STATUS] Backend is ONLINE! Health status:' $r.status } catch { Write-Host '[WAITING] Backend starting up in background...' }"

echo.
echo ========================================================
echo [DONE] The FastAPI backend is now permanently configured!
echo It will run silently in the background whenever Windows starts.
echo You can use the web app anytime at http://127.0.0.1:8000/ or
echo by opening index.html in your browser.
echo ========================================================
echo.
pause
