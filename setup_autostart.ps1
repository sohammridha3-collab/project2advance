$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ws = New-Object -ComObject WScript.Shell
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'HealthBridge_Backend.lnk'
$targetVbs = Join-Path $scriptDir 'start_backend_silent.vbs'

$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = "wscript.exe"
$sc.Arguments = "`"$targetVbs`""
$sc.WorkingDirectory = $scriptDir
$sc.Description = "HealthBridge AI FastAPI Backend Permanent Background Service"
$sc.Save()

Write-Host "[SUCCESS] Permanent Windows startup shortcut created at: $shortcutPath"
Write-Host "[INFO] Pointing to: $targetVbs"
