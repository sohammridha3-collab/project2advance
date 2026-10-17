@echo off
title Stop HealthBridge AI Backend
cd /d "%~dp0"

echo Setting stop signal for watchdog service...
echo stop > "%~dp0.stop_signal"

echo Stopping any running FastAPI / Uvicorn server on port 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$lines = netstat -ano | Select-String ':8000' | Select-String 'LISTENING'; " ^
  "if ($lines) { " ^
  "  $pids = $lines | ForEach-Object { ($_ -split '\s+')[-1] } | Select-Object -Unique; " ^
  "  foreach ($p in $pids) { " ^
  "    if ($p -match '^\d+$' -and $p -ne '0') { " ^
  "      Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; " ^
  "      Write-Host \"[KILLED] Stopped process PID $p on port 8000\"; " ^
  "    } " ^
  "  } " ^
  "} else { " ^
  "  Write-Host '[INFO] No process is currently listening on port 8000.'; " ^
  "}"

echo Done.
ping -n 2 127.0.0.1 >nul
