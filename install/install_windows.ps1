# ==============================================================================
# TrueTrack Windows Installer
# ==============================================================================

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Source Helpers
. "$ScriptDir\common\checks.ps1"
. "$ScriptDir\common\env_writer.ps1"
. "$ScriptDir\common\integration.ps1"

function Main {
    param(
        [switch]$DryRun
    )

    Write-LogInfo "Starting TrueTrack Installation..."

    # --------------------------------------------------------------------------
    # Phase 0 & 1: Checks & Dependencies
    # --------------------------------------------------------------------------
    Check-Preflight
    Install-Packages

    # --------------------------------------------------------------------------
    # Phase 2: Clone Repository
    # --------------------------------------------------------------------------
    $TargetDir = "$env:LOCALAPPDATA\TrueTrack"
    Write-LogInfo "Phase 2: Verifying Repository State at $TargetDir"

    if ($ProjectRoot -ne $TargetDir) {
        if (Test-Path $TargetDir) {
            Write-LogWarn "Target directory exists."
            $confirmation = Read-Host "Overwrite? (y/N)"
            if ($confirmation -ne "y") {
                Fail-Install "Aborted by user."
            }
            Remove-Item -Recurse -Force $TargetDir
        }

        Write-LogInfo "Cloning/Copying to $TargetDir..."
        # Copy current files (Assuming running from source package)
        New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
        Copy-Item -Recurse "$ProjectRoot\*" "$TargetDir"
        
        Write-LogSuccess "Repository installed."
        
        # Re-exec
        Write-LogInfo "Re-executing from target..."
        & "$TargetDir\install\install_windows.ps1"
        return
    }

    # --------------------------------------------------------------------------
    # Phase 3: Resolve OS-Specific Paths
    # --------------------------------------------------------------------------
    Write-LogInfo "Phase 3: Resolving Paths"
    
    $MusicRoot = "$env:USERPROFILE\Music"
    $DbPath = "$TargetDir\data\jobs.db"
    
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DbPath) | Out-Null
    New-Item -ItemType Directory -Force -Path $MusicRoot | Out-Null
    
    Write-LogSuccess "Paths resolved: Music=$MusicRoot, DB=$DbPath"

    # --------------------------------------------------------------------------
    # Phase 4: Write .env
    # --------------------------------------------------------------------------
    if ($DryRun) {
        Write-LogInfo "Dry Run: Skipping writes."
        return
    }

    Write-LogInfo "Phase 4: Configuring Environment"
    
    $EnvUpdates = @{
        "MUSIC_LIBRARY_ROOT" = $MusicRoot
        "TRUETRACK_DB_PATH" = $DbPath
    }
    
    Write-EnvFile -SourceFile "$TargetDir\.env.example" -TargetFile "$TargetDir\.env" -Updates $EnvUpdates

    # --------------------------------------------------------------------------
    # Phase 5: Project Setup
    # --------------------------------------------------------------------------
    Write-LogInfo "Phase 5: Project Setup"
    Set-Location $TargetDir

    # Python Venv
    if (Test-Path ".venv") {
        Remove-Item -Recurse -Force ".venv"
    }
    
    Write-LogInfo "Creating virtual environment..."
    python -m venv .venv
    
    # Activate
    . ".venv\Scripts\Activate.ps1"

    # Backend Deps
    Write-LogInfo "Installing Backend Dependencies..."
    pip install .

    # Frontend
    Write-LogInfo "Setting up Frontend..."
    Set-Location "frontend"
    pnpm install
    pnpm build
    Set-Location ".."

    # --------------------------------------------------------------------------
    # Phase 7: Integration
    # --------------------------------------------------------------------------
    Setup-Integration -InstallDir $TargetDir -DryRun:$DryRun

    # --------------------------------------------------------------------------
    # Phase 6: Verification
    # --------------------------------------------------------------------------
    Write-LogInfo "Phase 6: Verification"

    if (-not (Test-Path ".env")) { Fail-Install ".env missing" }
    if (-not (Test-Path $DbPath)) { New-Item $DbPath | Out-Null } # Simulate write
    if (-not (Test-Path "frontend\.next")) { Fail-Install "Frontend build missing" }

    Write-LogSuccess "TrueTrack Installed Successfully!"
    
    # --------------------------------------------------------------------------
    # Post-Install Message
    # --------------------------------------------------------------------------
    Write-Host "`nYou can start TrueTrack using:"
    Write-Host "  • Desktop launcher (if created)"
    Write-Host "  • Global command: truetrack"
    Write-Host "  • Manual: cd $TargetDir ; .\run.ps1"
    
    Write-Host "`nTrueTrack runs in your browser at:"
    Write-Host "  http://$env:TRUETRACK_HOST`:$env:TRUETRACK_PORT"
    
    Write-Host "`nTo stop: press Ctrl+C"
}

Main
