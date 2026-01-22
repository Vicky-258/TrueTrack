# ==============================================================================
# System Checks & Dependency Management (Windows)
# ==============================================================================

function Write-LogInfo {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-LogSuccess {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-LogWarn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-LogError {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Fail-Install {
    param([string]$Message)
    Write-LogError $Message
    exit 1
}

function Test-Admin {
    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Check-Preflight {
    Write-LogInfo "Phase 0: Preflight Checks"

    # OS Check (Implicit by running PS1, but check version?)
    $os = Get-CimInstance Win32_OperatingSystem
    Write-LogInfo "OS: $($os.Caption) ($($os.Version))"

    # Admin Check
    # Prompt says "Privilege Check".
    # winget often needs admin, though some user-scope installs work.
    # We'll fail if not admin to be deterministic.
    if (-not (Test-Admin)) {
        Fail-Install "Administrator privileges required. Please run as Administrator."
    }

    # Disk Space (C:)
    $disk = Get-PSDrive C | Where-Object {$_.Free -gt 2GB}
    if (-not $disk) {
        Fail-Install "Insufficient disk space on C:. Need at least 2GB free."
    }

    # Connectivity
    try {
        $null = Invoke-WebRequest -Uri "https://www.google.com" -Method Head -TimeoutSec 5 -ErrorAction Stop
    } catch {
        Fail-Install "No internet connectivity detected."
    }

    Write-LogSuccess "Preflight checks passed."
}

function Install-Packages {
    Write-LogInfo "Phase 1: Dependency Detection & Install"

    # Check Winget
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail-Install "Winget not found. Please install App Installer from Microsoft Store."
    }

    # Helper to check and install
    function Ensure-Package {
        param($Id, $Name, $CmdValidation)
        
        if (Get-Command $CmdValidation -ErrorAction SilentlyContinue) {
            Write-LogSuccess "$Name detected."
            return
        }

        Write-LogWarn "$Name not found. Installing via winget..."
        winget install --id $Id -e --accept-source-agreements --accept-package-agreements
        
        # Refresh path
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        if (-not (Get-Command $CmdValidation -ErrorAction SilentlyContinue)) {
            Fail-Install "Failed to install $Name ($Id)."
        }
    }

    # 1. GIT
    Ensure-Package -Id "Git.Git" -Name "Git" -CmdValidation "git"

    # 2. PYTHON 3.12+
    # Winget ID for Python 3.12 specifically or just "Python.Python.3"
    # We need >= 3.12.
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ([version]$pyVer -lt [version]"3.12") {
            Write-LogWarn "Python $pyVer too old. Installing Python 3.12..."
            winget install --id "Python.Python.3.12" -e --accept-source-agreements --accept-package-agreements
        } else {
            Write-LogSuccess "Python $pyVer detected."
        }
    } else {
        winget install --id "Python.Python.3.12" -e --accept-source-agreements --accept-package-agreements
    }

    # 3. UV (or Pip)
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-LogWarn "uv not found. Installing..."
        powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    }

    # 4. NODE (LTS) & PNPM
    Ensure-Package -Id "OpenJS.NodeJS.LTS" -Name "Node.js" -CmdValidation "node"
    
    if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
        Write-LogWarn "pnpm not found. Installing..."
        npm install -g pnpm
    }

    Write-LogSuccess "Dependencies installed."
}
