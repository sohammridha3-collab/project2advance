@echo off
cd /d "%~dp0"

:: Check if port 8000 is already active
netstat -ano | findstr LISTENING | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    exit /b 0
)

:: Locate Python 3.12 or system Python
set "PY_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY_EXE%" (
    set "PY_EXE=python"
)

:: Clear previous stop signal if present
if exist "%~dp0.stop_signal" del "%~dp0.stop_signal" >nul 2>&1

:: Watchdog loop: keeps FastAPI backend permanently online
:watchdog_loop
if exist "%~dp0.stop_signal" (
    echo [%date% %time%] [HealthBridge Service] Intentional stop requested. Service terminating. >> "%~dp0backend.log"
    del "%~dp0.stop_signal" >nul 2>&1
    exit /b 0
)

echo [%date% %time%] [HealthBridge Service] Starting FastAPI backend on http://127.0.0.1:8000 >> "%~dp0backend.log"
"%PY_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8000 >> "%~dp0backend.log" 2>&1

if exist "%~dp0.stop_signal" (
    echo [%date% %time%] [HealthBridge Service] Intentional stop detected. Service terminating. >> "%~dp0backend.log"
    del "%~dp0.stop_signal" >nul 2>&1
    exit /b 0
)

echo [%date% %time%] [HealthBridge Service] FastAPI backend stopped (Exit Code: %errorlevel%). Automatically restarting in 2 seconds... >> "%~dp0backend.log"
timeout /t 2 /nobreak >nul
goto watchdog_loop
