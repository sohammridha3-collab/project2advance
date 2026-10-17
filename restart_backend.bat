@echo off
title Restart HealthBridge AI Backend
cd /d "%~dp0"

echo Stopping port 8000...
call "%~dp0stop_backend.bat"

echo.
if exist "%~dp0.stop_signal" del "%~dp0.stop_signal" >nul 2>&1
echo Starting FastAPI in background...
wscript "%~dp0start_backend_silent.vbs"

echo Backend restarted.
ping -n 3 127.0.0.1 >nul
