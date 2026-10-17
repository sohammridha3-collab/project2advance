@echo off
title HealthBridge AI Backend Server
cd /d "%~dp0"
echo ========================================================
echo  HealthBridge AI - FastAPI Backend Server
echo  API Docs:  http://127.0.0.1:8000/docs
echo  Health:    http://127.0.0.1:8000/health
echo  App Home:  http://127.0.0.1:8000/
echo ========================================================

netstat -ano | findstr LISTENING | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] FastAPI backend is ALREADY running on port 8000!
    echo Opening browser to http://127.0.0.1:8000/...
    start http://127.0.0.1:8000/
    timeout /t 3 >nul
    exit /b 0
)

set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

echo Starting FastAPI Backend on http://127.0.0.1:8000...
echo [IMPORTANT] Keep this terminal window open while using the app!
echo ========================================================
"%PY_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload --reload-exclude "health_risk.db*" --reload-exclude "*.log" --reload-exclude "uploads/*" --reload-exclude "*.pyc" --reload-exclude ".git/*"
pause
