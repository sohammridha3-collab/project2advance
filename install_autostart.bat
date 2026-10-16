@echo off
title HealthBridge AI - Install Permanent Auto-Start
cd /d "%~dp0"

echo ========================================================
echo  HealthBridge AI - FastAPI Backend Auto-Start Setup
echo ========================================================
echo.
echo Installing background auto-start into Windows Startup folder...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_autostart.ps1"

echo.
echo ========================================================
echo  Starting FastAPI Backend in background right now...
echo ========================================================
wscript "%~dp0start_backend_silent.vbs"

echo.
echo [DONE] The FastAPI backend is now running and will auto-start
echo permanently whenever Windows boots up, keeping http://127.0.0.1:8000 online!
echo.
pause
