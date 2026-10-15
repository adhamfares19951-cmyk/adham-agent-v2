@echo off
chcp 65001 >nul
title Adham Agent - Self-Healing Watchdog 24/7
color 0A
cd /d "%~dp0"

echo ========================================================
echo        ADHAM-AGENT SELF-HEALING WATCHDOG SUPERVISOR
echo ========================================================

if exist "%~dp0python_runtime\python.exe" (
    set "PYTHON_EXE=%~dp0python_runtime\python.exe"
    echo [i] Python: Portable Runtime (Zero-install bundled)
    goto :RUN
)

if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
    echo [i] Python: Local Virtual Environment
    goto :RUN
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    echo [i] Python: System PATH Python
    goto :RUN
)

if exist "%~dp0python-3.13.16-amd64.exe" (
    echo [!] No Python detected. Installing bundled Python 3.13 silently...
    start /wait "" "%~dp0python-3.13.16-amd64.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    set "PYTHON_EXE=python"
    goto :RUN
)

echo [ERROR] No Python runtime or installer found!
pause
exit /b 1

:RUN
echo [i] Target: watchdog.py -^> main.py
echo [i] Auto-restart: ENABLED (24/7 Self-Healing)
echo ========================================================
"%PYTHON_EXE%" watchdog.py
pause