@echo off
title Stop HealthBridge AI Backend
cd /d "%~dp0"

echo Stopping any running FastAPI / Uvicorn server on port 8000...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$conns = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue; " ^
  "if ($conns) { " ^
  "  $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique; " ^
  "  foreach ($p in $pids) { " ^
  "    Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; " ^
  "    Write-Host \"[KILLED] Stopped process PID $p on port 8000\"; " ^
  "  } " ^
  "} else { " ^
  "  Write-Host '[INFO] No process is currently listening on port 8000.'; " ^
  "}"

echo Done.
timeout /t 2 >nul
