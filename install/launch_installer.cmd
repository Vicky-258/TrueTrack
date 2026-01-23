@echo off
SETLOCAL
:: =============================================================================
:: TrueTrack Installer Launcher
:: =============================================================================
:: This script safely launches the PowerShell installer with the correct policy.
:: It handles the case where double-clicking a .ps1 is mapped to Notepad.
:: =============================================================================

echo ---------------------------------------------------------------------------
echo   Launching TrueTrack Installer...
echo ---------------------------------------------------------------------------
echo.

:: Check for Administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process cmd -ArgumentList '/c, \"\"%~dp0%~nx0\"\" %* ' -Verb RunAs"
    exit /b
)

:: Run PowerShell Script
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows.ps1" %*

if %errorLevel% neq 0 (
    echo.
    echo ❌ Installer exited with error code %errorLevel%.
    echo.
    pause
    exit /b %errorLevel%
)

echo.
echo ✅ Installer finished. Exiting launcher...
timeout /t 5
