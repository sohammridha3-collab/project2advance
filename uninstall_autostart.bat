@echo off
title HealthBridge AI - Remove Backend Auto-Start Service
cd /d "%~dp0"

echo Removing background auto-start services...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$startup = [Environment]::GetFolderPath('Startup'); " ^
  "$shortcutPath = Join-Path $startup 'HealthBridge_Backend.lnk'; " ^
  "if (Test-Path $shortcutPath) { Remove-Item $shortcutPath -Force; Write-Host '[REMOVED] Startup shortcut deleted.' } else { Write-Host '[INFO] No startup shortcut found.' }"

schtasks /delete /tn "HealthBridge_FastAPI_Backend" /f >nul 2>&1
echo [REMOVED] Scheduled Task 'HealthBridge_FastAPI_Backend' removed (if existed).

echo.
echo Auto-start configuration removed.
pause
