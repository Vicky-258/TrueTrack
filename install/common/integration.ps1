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
    $BinDir = "$InstallDir\bin"
    if (-not (Test-Path $BinDir)) {
        New-Item -ItemType Directory -Force -Path $BinDir | Out-Null
    }
    
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
        Write-LogWarn "$BinDir is not in your User PATH. Add it manually or restart session to use 'truetrack' from CLI."
        # We can try to add it non-interactively, but modifying PATH without explicit consent is often frowned upon.
        # However, the prompt says "Must NOT modify system PATH". User PATH is somewhat safer but typically requires consent.
        # "If directory is not on PATH... require explicit consent".
        # But global rules "Installers must never wait for user input".
        # So we SKIP adding to PATH and just Warn.
    }

    # 2. Shortcuts (Desktop & Start Menu)
    # ---------------------------------------------------------
    $IconPath = "$InstallDir\assets\icon\truetrack.ico"
    if (-not (Test-Path $IconPath)) {
        Write-LogWarn "Icon assets not found. Shortcuts not created."
        return
    }

    $WshShell = New-Object -ComObject WScript.Shell
    
    # Function to create shortcut
    function Create-Shortcut {
        param($LinkPath, $Desc)
        try {
            $Shortcut = $WshShell.CreateShortcut($LinkPath)
            $Shortcut.TargetPath = "powershell.exe"
            $Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File `"$RunScript`""
            $Shortcut.WorkingDirectory = $InstallDir
            $Shortcut.IconLocation = "$IconPath"
            $Shortcut.Description = $Desc
            $Shortcut.Save()
            Write-LogSuccess "Created shortcut: $LinkPath"
        } catch {
            Write-LogWarn "Failed to create shortcut at $LinkPath"
        }
    }

    # Desktop
    $DesktopPath = [Environment]::GetFolderPath("Desktop")
    Create-Shortcut -LinkPath "$DesktopPath\TrueTrack.lnk" -Desc "Start TrueTrack"

    # Start Menu
    $StartMenuPath = [Environment]::GetFolderPath("StartMenu") # Programs folder usually better
    $StartMenuPrograms = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"
    if (Test-Path $StartMenuPrograms) {
        Create-Shortcut -LinkPath "$StartMenuPrograms\TrueTrack.lnk" -Desc "Start TrueTrack"
    } else {
         Write-LogWarn "Could not locate Start Menu Programs folder."
    }
}
