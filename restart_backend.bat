@echo off
title Restart HealthBridge AI Backend
cd /d "%~dp0"

echo Stopping port 8000...
call "%~dp0stop_backend.bat"

echo.
echo Starting FastAPI in background...
wscript "%~dp0start_backend_silent.vbs"

echo Backend restarted.
timeout /t 2 >nul
