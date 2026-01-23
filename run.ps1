# ==============================================================================
# TrueTrack Runtime Launcher (Windows)
# ==============================================================================

$ErrorActionPreference = "Stop"

# ----------------------------------------------------------------------
# Paths & Config
# ----------------------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$UserDataDir = "$env:LOCALAPPDATA\TrueTrack"
$PidDir = "$UserDataDir\pids"
$LogDir = "$UserDataDir\logs"

$ApiPidFile = "$PidDir\api.pid"
$WorkerPidFile = "$PidDir\worker.pid"
$FrontendPidFile = "$PidDir\frontend.pid"

$ApiLog = "$LogDir\api.log"
$WorkerLog = "$LogDir\worker.log"
$FrontendLog = "$LogDir\frontend.log"

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

function Get-RunningPid {
    param($PidFile)
    if (Test-Path $PidFile) {
        try {
            $Id = Get-Content $PidFile -ErrorAction Stop
            if ($Id) {
                $Proc = Get-Process -Id $Id -ErrorAction SilentlyContinue
                if ($Proc) {
                    return $Id
                }
            }
        } catch {}
    }
    return $null
}

function Start-BackgroundProcess {
    param($Command, $Args, $LogFile, $PidFile, $Name)

    Write-Host "Starting $Name..." -NoNewline
    
    # Fix: Cannot redirect both stdout and stderr to the same file handle directly in Start-Process.
    # We will redirect Output to LogFile, and Error to LogFile.err, or just let Error go to stream.
    # Better approach for "same log": Use cmd /c wrapper or just redirect output.
    # Let's use separate files to be safe and robust as per "God-Tier" standards.
    $LogFileErr = $LogFile + ".err"
    
    $Process = Start-Process -FilePath $Command -ArgumentList $Args `
        -RedirectStandardOutput $LogFile -RedirectStandardError $LogFileErr `
        -PassThru -WindowStyle Hidden

    $Process.Id | Out-File -FilePath $PidFile -Encoding ascii -NoNewline
    Write-Host " (PID $($Process.Id))"
}

# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------
$Command = if ($args) { $args[0].ToLower() } else { "start" }

switch ($Command) {
    "start" {
        # 1. Verify Venv
        if (-not (Test-Path ".venv")) {
            Write-Error "Virtual environment not found in $ScriptDir"
            exit 1
        }

        # 2. Create Dirs
        New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
        New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

        # 3. Check Running
        $Running = $false
        if (Get-RunningPid $ApiPidFile) { Write-Host "Backend already running."; $Running = $true }
        if (Get-RunningPid $WorkerPidFile) { Write-Host "Worker already running."; $Running = $true }
        if (Get-RunningPid $FrontendPidFile) { Write-Host "Frontend already running."; $Running = $true }

        if ($Running) {
            Write-Host "TrueTrack is already running. Use 'run.ps1 stop' to restart."
            exit 1
        }

        # 4. Environment
        $env:TRUETRACK_SKIP_FRONTEND = "1"
        $Python = "$ScriptDir\.venv\Scripts\python.exe"

        # Load .env (simplified)
        if (Test-Path ".env") {
            Get-Content ".env" | Foreach-Object {
                if ($_ -match "^([^#=]+)=(.*)$") {
                    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
                }
            }
        }

        # 5. Launch
        
        # Backend
        Start-BackgroundProcess -Command $Python -Args "app.py" `
            -LogFile $ApiLog -PidFile $ApiPidFile -Name "Backend"

        # Worker
        Start-BackgroundProcess -Command $Python -Args "worker/main.py" `
            -LogFile $WorkerLog -PidFile $WorkerPidFile -Name "Worker"

        # Frontend
        $NextServer = "$ScriptDir\frontend\.next\standalone\server.js"
        if (-not (Test-Path $NextServer)) {
            Write-Error "Frontend server.js not found. Run installer?"
            exit 1
        }
        
        $Node = "node" # Assume in path or installer added it
        $FrontendEnv = @{ PORT = "3001" } 
        # Note: Start-Process Environment support requires PS Core 7+ or manual block
        # Since we can't easily pass env vars to Start-Process in legacy PS, we rely on Process scope env.
        # We need to set PORT=3001 specifically for the frontend Node process.
        $env:PORT = "3001" 
        Start-BackgroundProcess -Command $Node -Args "`"$NextServer`"" `
            -LogFile $FrontendLog -PidFile $FrontendPidFile -Name "Frontend"
        Remove-Item Env:\PORT # Clean up

        Write-Host "`nTrueTrack started."
        $HostStr = if ($env:TRUETRACK_HOST) { $env:TRUETRACK_HOST } else { "127.0.0.1" }
        $PortStr = if ($env:TRUETRACK_PORT) { $env:TRUETRACK_PORT } else { "8000" }
        Write-Host "Web UI: http://${HostStr}:${PortStr}"
    }

    "stop" {
        Write-Host "Stopping TrueTrack..."
        $Stopped = $false

        function Stop-Component {
            param($Name, $PidFile)
            $Id = Get-RunningPid $PidFile
            if ($Id) {
                Write-Host "Stopping $Name ($Id)..."
                Stop-Process -Id $Id -Force -ErrorAction SilentlyContinue
                Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
                $script:Stopped = $true
            } elseif (Test-Path $PidFile) {
                Remove-Item $PidFile -Force # Stale
            }
        }

        Stop-Component "Backend" $ApiPidFile
        Stop-Component "Worker" $WorkerPidFile
        Stop-Component "Frontend" $FrontendPidFile

        if ($Stopped) {
            Write-Host "TrueTrack stopped."
        } else {
            Write-Host "TrueTrack was not running."
        }
    }

    "status" {
        Write-Host "TrueTrack Status"
        Write-Host "----------------"
        
        $AnyRunning = $false

        function Check-Component {
            param($Name, $PidFile)
            $Id = Get-RunningPid $PidFile
            if ($Id) {
                Write-Host "$Name`t: RUNNING (PID $Id)"
                $script:AnyRunning = $true
            } else {
                Write-Host "$Name`t: STOPPED"
            }
        }

        Check-Component "Backend" $ApiPidFile
        Check-Component "Worker" $WorkerPidFile
        Check-Component "Frontend" $FrontendPidFile
        
        Write-Host "----------------"
        
        if ($AnyRunning) {
             # Load .env for display
            if (Test-Path ".env") {
                Get-Content ".env" | Foreach-Object {
                    if ($_ -match "^([^#=]+)=(.*)$") {
                        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
                    }
                }
            }
            $HostStr = if ($env:TRUETRACK_HOST) { $env:TRUETRACK_HOST } else { "127.0.0.1" }
            $PortStr = if ($env:TRUETRACK_PORT) { $env:TRUETRACK_PORT } else { "8000" }
            Write-Host "Web UI: http://${HostStr}:${PortStr}"
        }
    }

    { $_ -in "help", "--help", "-h", "/?" } {
        Write-Host "TrueTrack Manager"
        Write-Host "-----------------"
        Write-Host "Usage: .\run.ps1 [command]"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  start   Start TrueTrack (Backend, Worker, Frontend)"
        Write-Host "  stop    Stop all TrueTrack processes"
        Write-Host "  status  Show process status and Web UI URL"
        Write-Host "  help    Show this help message"
        Write-Host ""
        Write-Host "Environment Variables (optional):"
        Write-Host "  TRUETRACK_HOST      Host to bind (default: 127.0.0.1)"
        Write-Host "  TRUETRACK_PORT      Port for Web UI (default: 8000)"
        Write-Host "  TRUETRACK_DB_PATH   Path to SQLite DB"
    }

    default {
        Write-Host "Usage: .\run.ps1 [start|stop|status|help]"
        exit 1
    }
}
