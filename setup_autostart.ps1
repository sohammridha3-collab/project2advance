$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = "C:\Users\Sayan Mridha\Desktop\project2advance" }
$ws = New-Object -ComObject WScript.Shell
$targetVbs = Join-Path $scriptDir 'start_backend_silent.vbs'
$runAppBat = Join-Path $scriptDir 'run_app.bat'

# 1. Permanent Windows Startup Shortcut (Runs silently at logon)
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'HealthBridge_Backend.lnk'
$sc = $ws.CreateShortcut($shortcutPath)
$sc.TargetPath = "wscript.exe"
$sc.Arguments = "`"$targetVbs`""
$sc.WorkingDirectory = $scriptDir
$sc.Description = "HealthBridge AI FastAPI Backend Permanent Background Service"
$sc.Save()
Write-Host "[SUCCESS] Windows Startup folder shortcut created: $shortcutPath"

# 2. Windows Task Scheduler Task (If running as administrator)
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    try {
        $action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$targetVbs`"" -WorkingDirectory $scriptDir
        $trigger = New-ScheduledTaskTrigger -AtLogOn
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Days 0)
        Register-ScheduledTask -TaskName "HealthBridge_FastAPI_Backend" -Action $action -Trigger $trigger -Settings $settings -Description "HealthBridge AI FastAPI Permanent Service" -Force | Out-Null
        Write-Host "[SUCCESS] Windows Scheduled Task 'HealthBridge_FastAPI_Backend' registered."
    } catch {
        # optional
    }
} else {
    Write-Host "[INFO] User-level Startup service active (launches automatically whenever Windows starts)."
}

# 3. Convenient Desktop Shortcut for 1-Click Launch
try {
    $desktop = [Environment]::GetFolderPath('Desktop')
    $desktopShortcut = Join-Path $desktop 'HealthBridge AI.lnk'
    $dsc = $ws.CreateShortcut($desktopShortcut)
    $dsc.TargetPath = $runAppBat
    $dsc.WorkingDirectory = $scriptDir
    $dsc.Description = "Launch HealthBridge AI Platform (FastAPI + Web UI)"
    $dsc.Save()
    Write-Host "[SUCCESS] Desktop shortcut created: $desktopShortcut"
} catch {
    Write-Host "[INFO] Desktop shortcut creation skipped."
}

# 4. Trigger silent start immediately if not running
Start-Process -FilePath "wscript.exe" -ArgumentList "`"$targetVbs`"" -WorkingDirectory $scriptDir
Write-Host "[INFO] FastAPI backend start triggered successfully."
