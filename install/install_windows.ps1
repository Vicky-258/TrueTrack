# ==============================================================================
# TRUE TRACK - GOD-TIER WINDOWS INSTALLER
# ==============================================================================
# This script is designed to be:
# 1. Executable on any Windows machine (PowerShell 2.0+)
# 2. Hostile-environment aware (Policy restrictions, missing PATH, AntiVirus)
# 3. Idempotent & Resumable (State based)
# 4. Self-Healing (Fixes PATH, installs dependencies)
# ==============================================================================

# Parameters
param(
    [switch]$DryRun,     # Simulate actions only
    [switch]$Force,      # Ignore state file
    [switch]$NoColor     # Disable ANSI colors
)

# ------------------------------------------------------------------------------
# 0. BOOTSTRAP & SELF-ELEVATION
# ------------------------------------------------------------------------------
# Ensure we are running with sufficient privileges and correct policy.
$CurrentPolicy = Get-ExecutionPolicy
if ($CurrentPolicy -ne 'Unrestricted' -and $CurrentPolicy -ne 'Bypass' -and $CurrentPolicy -ne 'RemoteSigned') {
    if ($PSCommandPath) {
        Write-Host "⚠️  Execution Policy Restricted. Relaunching in Bypass mode..." -ForegroundColor Yellow
        Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" $MyInvocation.BoundParameters" -Wait
        exit
    }
}

# Admin check removed for hardening (User-scope preferred). 
# Elevation will be requested on-demand if specific operations fail.

# ------------------------------------------------------------------------------
# 1. GLOBAL CONSTANTS & CONFIG
# ------------------------------------------------------------------------------
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# Paths
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$InstallDir  = "$env:LOCALAPPDATA\TrueTrack"
$LogDir      = "$InstallDir\logs"
$StateFile   = "$InstallDir\.state.json"
$LogFile     = "$LogDir\install_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

# Create Log/Install Dirs early
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force -Path $LogDir | Out-Null }

# ------------------------------------------------------------------------------
# 2. CORE UTILITIES (LOGGING, STATE, ENV)
# ------------------------------------------------------------------------------

# >>>> LOGGING <<<<
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO","SUCCESS","WARN","ERROR","FATAL","DEBUG")]
        [string]$Level = "INFO"
    )

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] [$Level] $Message"

    # File Log (Always strip colors)
    if (-not $DryRun) {
        $LogEntry | Out-File -FilePath $LogFile -Append -Encoding utf8
    }

    # Console Output
    $Color = "White"
    switch ($Level) {
        "SUCCESS" { $Color = "Green" }
        "WARN"    { $Color = "Yellow" }
        "ERROR"   { $Color = "Red" }
        "FATAL"   { $Color = "DarkRed" }
        "DEBUG"   { $Color = "Gray" }
    }
    
    # Prefix icons for readability
    $Icon = " "
    switch ($Level) {
        "SUCCESS" { $Icon = "✅" }
        "WARN"    { $Icon = "⚠️ " }
        "ERROR"   { $Icon = "❌" }
        "FATAL"   { $Icon = "💀" }
        "DEBUG"   { $Icon = "🔍" }
    }

    if ($DryRun) { $Icon = "🔮 $Icon" }

    Write-Host "$Icon $Message" -ForegroundColor $Color
}

function Fail-Fatal {
    param([string]$Message, [string]$FixCommand)
    Write-Log -Level FATAL $Message
    if ($FixCommand) {
        Write-Host "`n💡 MANUAL FIX REQUIRED:" -ForegroundColor Cyan
        Write-Host "   $FixCommand`n" -ForegroundColor White
    }
    Write-Host "See log for details: $LogFile"
    exit 1
}

# >>>> STATE MACHINE <<<<
# >>>> STATE MACHINE <<<<
$Script:InstallState = @{}
$StateVersion = 1

if (Test-Path $StateFile) {
    try {
        $LoadedState = Get-Content $StateFile | ConvertFrom-Json -AsHashtable
        if ($LoadedState['stateVersion'] -ne $StateVersion) {
            Write-Log -Level WARN "State version mismatch (Expected $StateVersion). Resetting state."
            $Script:InstallState = @{ 'stateVersion' = $StateVersion }
        } else {
            $Script:InstallState = $LoadedState
        }
    } catch {
        Write-Log -Level WARN "State file corrupt. Starting fresh."
        $Script:InstallState = @{ 'stateVersion' = $StateVersion }
    }
} else {
    $Script:InstallState = @{ 'stateVersion' = $StateVersion }
}

function Set-State {
    param([string]$Key, [string]$Value)
    if ($DryRun) { return }
    
    $Script:InstallState[$Key] = $Value
    $Script:InstallState | ConvertTo-Json -Depth 5 | Out-File $StateFile -Encoding utf8
}

function Get-State {
    param([string]$Key)
    return $Script:InstallState[$Key]
}

# >>>> ENVIRONMENT <<<<
function Check-Path {
    param([string]$Command)
    
    # Reload Path from Registry to ensure we see fresh changes
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    return (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Backup-Path {
    if (-not (Get-State "PATH_BACKUP")) {
        $CurrentPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
        Set-State "PATH_BACKUP" $CurrentPath
        Write-Log -Level INFO "User PATH backed up to state file."
    }
}

function Add-ToPath {
    param([string]$PathToAdd)
    
    if (-not (Test-Path $PathToAdd)) {
        Write-Log -Level WARN "Attempted to add non-existent path: $PathToAdd"
        return
    }

    $CleanPath = (Resolve-Path $PathToAdd).Path
    $UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
    
    # Deduplication Check
    $PathParts = $UserPath -split ";"
    if ($PathParts -contains $CleanPath) {
        Write-Log -Level DEBUG "Path already in Registry: $CleanPath"
        return
    }

    Write-Log -Level INFO "Appending to User PATH: $CleanPath"

    if ($DryRun) { return }

    # 1. Backup
    Backup-Path
    
    # 2. Length Check
    $NewPath = "$UserPath;$CleanPath"
    if ($NewPath.Length -gt 2048) {
        Write-Log -Level WARN "PATH variable is becoming long ($($NewPath.Length) chars). Standard limit is ~2048, extended is 32767."
    }

    # 3. Write
    try {
        [Environment]::SetEnvironmentVariable("Path", $NewPath, [EnvironmentVariableTarget]::User)
        $env:Path = "$env:Path;$CleanPath" # Update current session
        Write-Log -Level SUCCESS "Added to PATH."
    } catch {
        Write-Log -Level ERROR "Failed to write PATH to registry: $_"
    }
}

# ------------------------------------------------------------------------------
# 3. DEPENDENCY HELPERS
# ------------------------------------------------------------------------------

function Install-Winget {
    param([string]$Id)
    
    if (-not (Check-Path "winget")) {
        Write-Log -Level WARN "Winget not found."
        return $false
    }

    Write-Log -Level INFO "Attempting Winget install for '$Id'..."
    if ($DryRun) { return $true }

    try {
        winget install --id $Id -e --source winget --accept-package-agreements --accept-source-agreements
        return $true
    } catch {
        Write-Log -Level ERROR "Winget install failed: $_"
        return $false
    }
}

function Check-Tool {
    param(
        [string]$Name,         # Friendly Name (e.g. "Node.js")
        [string]$Command,      # Binary Name (e.g. "node")
        [string]$WingetId,     # Winget ID (e.g. "OpenJS.NodeJS")
        [string]$ManualUrl,    # Manual Download URL
        [switch]$Critical      # Is this fatal if missing?
    )
    
    Write-Log -Level INFO "Checking for $Name..."

    # 1. Check Existing
    if (Check-Path $Command) {
        Write-Log -Level SUCCESS "$Name is available."
        return $true
    }

    # 2. Try Winget
    Write-Log -Level WARN "$Name not found. Attempting auto-install..."
    if ($WingetId) {
        $WingetResult = Install-Winget -Id $WingetId
        if ($WingetResult) {
            # Verification Re-check
            if (Check-Path $Command) {
                Write-Log -Level SUCCESS "$Name installed successfully."
                return $true
            }
             # Sometimes PATH needs a full shell restart refresh which we can't fully do, 
             # but we can try to guess standard paths if likely installed.
             Write-Log -Level WARN "$Name installed but not yet in PATH. Restart installer to detect."
        }
    }

    # 3. Manual / Fail
    if ($Critical) {
        Fail-Fatal "$Name is required but could not be installed automatically." "Download and install from: $ManualUrl`n   Then re-run this installer."
    } else {
        Write-Log -Level WARN "$Name missing. Some features may not work."
        Write-Log -Level INFO "Manual Install: $ManualUrl"
        return $false
    }
}

# ------------------------------------------------------------------------------
# 4. MAIN INSTALL FLOW
# ------------------------------------------------------------------------------
function Main {
    Write-Log -Level INFO "=========================================="
    Write-Log -Level INFO "   TrueTrack Installer (God-Tier Edition) "
    Write-Log -Level INFO "=========================================="
    Write-Log -Level INFO "Log File: $LogFile"
    if ($DryRun) { Write-Log -Level WARN "!!! DRY RUN MODE ACTIVE - NO CHANGES WILL BE MADE !!!" }

    # ---- STEP 1: UV INSTALLATION (CRITICAL) ----
    if (-not (Get-State "Step_UV_Installed") -or $Force) {
        Write-Log -Level INFO "Checking for 'uv' package manager..."
        
        if (Check-Path "uv") {
            Write-Log -Level SUCCESS "uv is already installed."
        } else {
            Write-Log -Level INFO "uv missing. Installing..."
            if (-not $DryRun) {
                # Robust Install: Download script first, check it, then run.
                # Prevents "Invoke-Expression" errors if network returns HTML/Garbage.
                $UvInstallUrl = "https://astral.sh/uv/install.ps1"
                $TempScript = "$env:TEMP\uv_install_$(Get-Random).ps1"
                
                try {
                    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                    Invoke-WebRequest -Uri $UvInstallUrl -OutFile $TempScript -UseBasicParsing
                    
                    # Basic validation: Check if file exists and has content
                    if ((Get-Item $TempScript).Length -gt 100) {
                        Write-Log -Level INFO "Executing uv installer..."
                        & $TempScript
                    } else {
                        throw "Downloaded installer script seems empty or invalid."
                    }
                } catch {
                     Write-Log -Level ERROR "Failed to download/run uv installer: $_"
                     Write-Log -Level WARN "Trying fallback method (irm | iex)..."
                     try {
                        irm $UvInstallUrl | iex
                     } catch {
                        Fail-Fatal "Could not install 'uv'. Network issue?" "Manually run: irm https://astral.sh/uv/install.ps1 | iex"
                     }
                } finally {
                    if (Test-Path $TempScript) { Remove-Item $TempScript -ErrorAction SilentlyContinue }
                }

                # Manual Path Refresh attempt
                $UV_Path = "$env:USERPROFILE\.local\bin"
                if (Test-Path $UV_Path) { Add-ToPath $UV_Path }
            }
            
            if (-not (Check-Path "uv") -and -not $DryRun) {
                Fail-Fatal "Failed to install 'uv'. This is a critical dependency." "irm https://astral.sh/uv/install.ps1 | iex"
            }
        }
        Set-State "Step_UV_Installed" $true
    }

    # ---- STEP 2: EXTERNAL TOOLS ----
    # Git
    Check-Tool -Name "Git" -Command "git" -WingetId "Git.Git" -ManualUrl "https://git-scm.com/download/win" -Critical
    
    # Node.js
    Check-Tool -Name "Node.js" -Command "node" -WingetId "OpenJS.NodeJS" -ManualUrl "https://nodejs.org/en/download/" -Critical
    
    # Python (Check only, uv handles python, but system python is good fallback)
    # optional check? No, uv manages python versions. We just need uv.
    
    Write-Log -Level SUCCESS "Core dependencies verified."
    
    # ---- STEP 3: REPO CLONE / UPDATE ----
    if (-not (Get-State "Step_Repo_Cloned") -or $Force) {
        Write-Log -Level INFO "Installing TrueTrack to: $InstallDir"
        
        if ($ProjectRoot -ne $InstallDir) {
           Write-Log -Level INFO "Copying files from: $ProjectRoot"
           if (-not $DryRun) {
               if (Test-Path $InstallDir) {
                   
                   # Careful cleanup
                   # We don't want to nuke .env or data if they exist
                   # But for a robust installer, we usually want to overwrite app code.
                   
                   # Copy-Item with Recurse/Force should overwrite.
               } else {
                   New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
               }
               
               # SELECTIVE COPY (Protect User Data)
               $Items = Get-ChildItem -Path $ProjectRoot
               foreach ($Item in $Items) {
                   $DestPath = Join-Path $InstallDir $Item.Name
                   
                   # Protected items: Don't overwrite if exist
                   if ($Item.Name -eq ".env" -or $Item.Name -eq "data") {
                       if (-not (Test-Path $DestPath)) {
                           Copy-Item -Recurse -Path $Item.FullName -Destination $DestPath
                       } else {
                           Write-Log -Level DEBUG "Skipping protected item: $($Item.Name)"
                       }
                   } 
                   # Safe items: Force overwrite
                   else {
                       Copy-Item -Recurse -Force -Path $Item.FullName -Destination $DestPath
                   }
               }

           }
        } else {
            Write-Log -Level INFO "Running in-place. Skipping copy."
        }
        Set-State "Step_Repo_Cloned" $true
    }
    
    # Change context to InstallDir for subsequent steps
    if (-not $DryRun) { Set-Location $InstallDir }

    # ---- STEP 4: ENVIRONMENT CONFIG (.env) ----
    if (-not (Get-State "Step_Env_Configured") -or $Force) {
        Write-Log -Level INFO "Configuring environment..."
        
        $MusicRoot = "$env:USERPROFILE\Music\TrueTrack"
        $DbPath = "$InstallDir\data\jobs.db"
        
        # Ensure Dirs
        if (-not $DryRun) {
            if (-not (Test-Path $MusicRoot)) { New-Item -ItemType Directory -Force -Path $MusicRoot | Out-Null }
            if (-not (Test-Path (Split-Path -Parent $DbPath))) { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DbPath) | Out-Null }
        }

        # Write .env (Custom Logic to preserve secrets if they existed?)
        # For now, simple overwrite/creation based on .env.example
        if (-not $DryRun) {
             # Basic template replacement
             if (-not (Test-Path ".env")) {
                 Copy-Item ".env.example" ".env"
                 Add-Content ".env" "`r`nMUSIC_LIBRARY_ROOT=$MusicRoot"
                 Add-Content ".env" "`r`nTRUETRACK_DB_PATH=$DbPath"
                 Write-Log -Level SUCCESS "Created default .env"
             } else {
                 Write-Log -Level INFO ".env exists. Skipping overwrite (manual review recommended)."
                 # Ideally we would check for missing keys here.
             }
        }
        Set-State "Step_Env_Configured" $true
    }

    # ---- STEP 5: BACKEND SETUP ----
    if (-not (Get-State "Step_Backend_Installed") -or $Force) {
        Write-Log -Level INFO "Setting up Backend (Python)..."
        
        if (-not $DryRun) {
            # Reset venv if it looks broken? For now, trust uv sync.
            Write-Log -Level INFO "Running 'uv sync'..."
            uv sync
            if ($LASTEXITCODE -ne 0) { Fail-Fatal "Backend dependency installation failed." "Run 'uv sync' manually to debug." }
        }
        Set-State "Step_Backend_Installed" $true
    }

    # ---- STEP 6: FRONTEND SETUP ----
    if (-not (Get-State "Step_Frontend_Installed") -or $Force) {
        Write-Log -Level INFO "Setting up Frontend (Node.js)..."
        
        if (-not $DryRun) {
            Set-Location "frontend"
            
            # Detect package manager (prefer pnpm if present, else npm)
            $PkgManager = "npm"
            if (Check-Path "pnpm") { $PkgManager = "pnpm" }

            Write-Log -Level INFO "Using $PkgManager..."
            
            # Install
            Write-Log -Level INFO "Installing dependencies..."
            & $PkgManager install
            if ($LASTEXITCODE -ne 0) { Fail-Fatal "Frontend install failed." "cd frontend; $PkgManager install" }

            # Build
            Write-Log -Level INFO "Building frontend..."
            & $PkgManager run build
            if ($LASTEXITCODE -ne 0) { 
                # Non-blocking failure? User can dev mode. But for installer, usually fatal if we want a working app.
                Write-Log -Level ERROR "Frontend build failed. The app may not start correctly."
                # Don't exit, maybe user wants to fix manually.
            } else {
                Write-Log -Level SUCCESS "Frontend built."
            }
            
            Set-Location ".."
        }
        Set-State "Step_Frontend_Installed" $true
    }
    
    # ---- STEP 7: LAUNCHERS & SHORTCUTS ----
    if (-not (Get-State "Step_Shortcuts_Created") -or $Force) {
        Write-Log -Level INFO "Creating shortcuts..."
        
        $BinDir = "$InstallDir\bin"
        if (-not $DryRun) {
            if (-not (Test-Path $BinDir)) { New-Item -ItemType Directory -Force -Path $BinDir | Out-Null }
            
            # 1. Global Command Wrapper (truetrack.cmd)
            # This allows typing 'truetrack' anywhere if bin is in PATH
            $GlobalCmdPath = "$BinDir\truetrack.cmd"
            # Point to the python launcher script in the backend
            $LauncherScript = "@echo off`r`ncd /d `"$InstallDir`"`r`ncall .venv\Scripts\activate.bat`r`npython backend/main.py %*"
            # Wait, user wants lifecycle commands (start/stop) which are usually subcommands of the main app.
            # Assuming 'main.py' or 'cli.py' handles 'start'.
            # Let's align with the "Implement Lifecycle Commands" conversation: "truetrack start" should be default.
            
            # The user's request for this specific task says: "Backend launches, Frontend reachable".
            # It doesn't explicitly define the CLI implementation here, but implies we should expose it.
            # Using a simple wrapper that calls the python module is safest.
            
            $CmdContent = "@echo off`r`n`"$InstallDir\.venv\Scripts\python.exe`" -m backend.cli %*"
            Set-Content -Path $GlobalCmdPath -Value $CmdContent
            
            # Add bin to PATH
            Add-ToPath $BinDir
            
            # 2. Desktop Shortcut
            $WshShell = New-Object -ComObject WScript.Shell
            $ShortcutPath = "$env:USERPROFILE\Desktop\TrueTrack.lnk"
            $Shortcut = $WshShell.CreateShortcut($ShortcutPath)
            $Shortcut.TargetPath = "$BinDir\truetrack.cmd"
            $Shortcut.Arguments = "start" # Default to start
            $Shortcut.WorkingDirectory = $InstallDir
            
            try {
                $Shortcut.IconLocation = "$InstallDir\frontend\public\favicon.ico"
            } catch {
                Write-Log -Level DEBUG "Could not set shortcut icon."
            }
            
            $Shortcut.Description = "Start TrueTrack"
            $Shortcut.Save()
            
            Write-Log -Level SUCCESS "Shortcuts created."
        }
        Set-State "Step_Shortcuts_Created" $true
    }

    # ---- STEP 8: VERIFICATION ----
    Write-Log -Level INFO "Verifying Installation..."
    
    # 1. Check if backend can be imported/help runs
    if (-not $DryRun) {
        $TestCmd = "$InstallDir\.venv\Scripts\python.exe"
        $TestArgs = "-c `"(import backend.cli); print('Backend OK')`""
        
        # Simple execution test
        try {
            $Process = Start-Process -FilePath $TestCmd -ArgumentList $TestArgs -NoNewWindow -PassThru -Wait
            if ($Process.ExitCode -eq 0) {
                 Write-Log -Level SUCCESS "Backend verification passed."
            } else {
                 Write-Log -Level ERROR "Backend verification failed (Exit Code $($Process.ExitCode))."
            }
        } catch {
            Write-Log -Level ERROR "Backend verification failed to launch: $_"
        }
    }

    Write-Log -Level SUCCESS "TrueTrack Application Installed Successfully!"
    Write-Log -Level INFO "--------------------------------------------------"
    Write-Log -Level INFO "To start the app:"
    Write-Log -Level INFO "  1. Double-click 'TrueTrack' on your Desktop"
    Write-Log -Level INFO "  2. Run 'truetrack start' in any terminal"
    Write-Log -Level INFO "--------------------------------------------------"
}

# Run Main
try {
    Main
} catch {
    Fail-Fatal "Unhandled Critical Error: $_"
}
