@echo off
chcp 65001 > nul
title Adham Agent Enterprise Agency OS
color 0A

echo ==============================================================================
echo 🏛️  ADHAM AGENT ENTERPRISE AGENCY OS - LAUNCHER
echo ==============================================================================
echo [INFO] Setting up execution environment...

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARN] Virtual environment not found, running with system python...
)

set PYTHONIOENCODING=utf-8
set WEB_PORT=8080

echo [INFO] Launching Unified Services (FastAPI Web + Telegram Bot + Gateway)...
echo.
python run_agency_os.py

echo.
echo [INFO] Agency OS session ended.
pause
