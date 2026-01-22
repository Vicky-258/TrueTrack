# ==============================================================================
# Integration Helpers (Windows)
# ==============================================================================

function Setup-Integration {
    param(
        [string]$InstallDir,
        [switch]$DryRun
    )

    Write-LogInfo "Phase 7: Integration & Desktop Shortcuts"
    $RunScript = "$InstallDir\run.ps1"

    if ($DryRun) {
        Write-LogInfo "Dry run: Skipping integration setup."
        return
    }

    # 1. Global Launcher
    # ---------------------------------------------------------
    Write-Host "`nCreate global global command 'truetrack'? (y/N)" -NoNewline
    $response = Read-Host
    if ($response -eq "y") {
        $BinDir = "$InstallDir\bin"
        New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
        
        $LauncherPs1 = "$BinDir\truetrack.ps1"
        $LauncherCmd = "$BinDir\truetrack.cmd"

        # PS1 Launcher
        $content = @"
Set-Location "$InstallDir"
& ".\run.ps1" `$args
"@
        Set-Content -Path $LauncherPs1 -Value $content

        # CMD Shim
        $cmdContent = @"
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0truetrack.ps1" %*
"@
        Set-Content -Path $LauncherCmd -Value $cmdContent
        
        Write-LogSuccess "Created launcher at $LauncherPs1"

        # PATH Check (User Scope)
        $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($UserPath -notlike "*$BinDir*") {
            Write-Host "`nAdd $BinDir to User PATH? (y/N)" -NoNewline
            $pathResp = Read-Host
            if ($pathResp -eq "y") {
                [Environment]::SetEnvironmentVariable("Path", $UserPath + ";$BinDir", "User")
                $env:Path += ";$BinDir"
                Write-LogSuccess "Added to User PATH."
            }
        }
    }

    # 2. Desktop Shortcut
    # ---------------------------------------------------------
    $IconPath = "$InstallDir\assets\icon\truetrack.ico"
    if (-not (Test-Path $IconPath)) {
        Write-LogWarn "Icon assets not found. Desktop launcher not created."
        return
    }

    Write-Host "`nCreate desktop launcher? (y/N)" -NoNewline
    $respShortcut = Read-Host
    if ($respShortcut -eq "y") {
        $DesktopPath = [Environment]::GetFolderPath("Desktop")
        $ShortcutPath = "$DesktopPath\TrueTrack.lnk"
        
        $WshShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
        
        # Target PowerShell to run the script
        $Shortcut.TargetPath = "powershell.exe"
        $Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""
        $Shortcut.WorkingDirectory = $InstallDir
        $Shortcut.IconLocation = "$IconPath"
        $Shortcut.Description = "Start TrueTrack"
        
        $Shortcut.Save()
        Write-LogSuccess "Created shortcut on Desktop."
    }
}
