@echo off
title Install Adham Agent as Windows Background Boot Service
color 0B
cd /d "%~dp0\..\.."

echo ===================================================================
echo     INSTALL ADHAM AGENT 24/7 WINDOWS TASK SCHEDULER SERVICE
echo ===================================================================
echo This will create a Windows Scheduled Task that launches the
echo Self-Healing Watchdog automatically whenever the computer/server boots.
echo.

set SCRIPT_PATH=%CD%\start_watchdog_hidden.vbs

echo Target: %SCRIPT_PATH%
echo.

schtasks /Create /TN "AdhamAgentWatchdog" /TR "wscript.exe \"%SCRIPT_PATH%\"" /SC ONSTART /RU "SYSTEM" /RL HIGHEST /F

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Windows Task 'AdhamAgentWatchdog' installed successfully!
    echo The bot will start automatically on every Windows boot 24/7.
    echo.
    echo Starting the task now...
    schtasks /Run /TN "AdhamAgentWatchdog"
) else (
    echo.
    echo [NOTE] If running as SYSTEM failed, trying with current user credentials...
    schtasks /Create /TN "AdhamAgentWatchdog" /TR "wscript.exe \"%SCRIPT_PATH%\"" /SC ONLOGON /RL HIGHEST /F
    schtasks /Run /TN "AdhamAgentWatchdog"
)

pause
