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

:: Run FastAPI Uvicorn and append logs
"%PY_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8000 >> "%~dp0backend.log" 2>&1
