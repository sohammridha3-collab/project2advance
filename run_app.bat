@echo off
title HealthBridge AI - Health Risk Prediction System
cd /d "%~dp0"

echo ========================================================
echo  HealthBridge AI - Health Continuity Platform
echo ========================================================

:: 1. Verify Python availability
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ from https://python.org
    echo and ensure "Add python.exe to PATH" is checked during setup.
    pause
    exit /b 1
)

:: 2. Check if server is already running on port 8000
powershell -NoProfile -Command "$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; if ($conn) { exit 0 } else { exit 1 }"
if %errorlevel% equ 0 (
    echo [INFO] FastAPI backend is ALREADY running on http://127.0.0.1:8000.
    echo Launching web application in your browser...
    start http://127.0.0.1:8000/
    timeout /t 2 >nul
    exit /b 0
)

:: 3. Verify and install dependencies if needed
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required Python dependencies from requirements.txt...
    python -m pip install -r requirements.txt
)

echo Starting FastAPI Backend on http://127.0.0.1:8000/ ...
echo Local Server: http://127.0.0.1:8000/
echo Swagger Docs: http://127.0.0.1:8000/docs
echo ========================================================
echo [IMPORTANT] Keep this terminal window open while using the app!
echo ========================================================

:: 4. Launch background health waiter that opens browser as soon as server is ready
start /b powershell -NoProfile -Command "for ($i=0; $i -lt 40; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { Start-Process 'http://127.0.0.1:8000/'; break } } catch { Start-Sleep -Milliseconds 400 } }"

:: 5. Run Uvicorn
python -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
