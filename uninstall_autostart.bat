@echo off
title HealthBridge AI - Remove Backend Auto-Start
cd /d "%~dp0"

echo Removing background auto-start shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$startup = [Environment]::GetFolderPath('Startup'); " ^
  "$shortcutPath = Join-Path $startup 'HealthBridge_Backend.lnk'; " ^
  "if (Test-Path $shortcutPath) { Remove-Item $shortcutPath -Force; Write-Host '[REMOVED] Startup shortcut deleted.' } else { Write-Host '[INFO] No startup shortcut was found.' }"

pause
