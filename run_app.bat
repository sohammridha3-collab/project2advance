@echo off
title AI Health Risk Prediction System
cd /d "%~dp0"

echo ========================================================
echo  AI-Based Health Risk Prediction System
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

:: 2. Verify and install dependencies if needed
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required Python dependencies from requirements.txt...
    python -m pip install -r requirements.txt
)

echo  Starting FastAPI Backend & loading 120MB ML model...
echo  Local Server: http://127.0.0.1:8000/
echo  Swagger Docs: http://127.0.0.1:8000/docs
echo ========================================================
echo  [WAIT] Initializing database and ML engine...
echo  [IMPORTANT] Keep this terminal window open while using the app!
echo ========================================================

:: 3. Launch background health waiter that opens browser ONLY when server is 200 OK
start /b powershell -NoProfile -Command "for ($i=0; $i -lt 40; $i++) { try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 1; if ($r.StatusCode -eq 200) { Start-Process 'http://127.0.0.1:8000/login.html'; break } } catch { Start-Sleep -Milliseconds 500 } }"

:: 4. Run Uvicorn
python -m uvicorn main:app --host 127.0.0.1 --port 8000

pause

