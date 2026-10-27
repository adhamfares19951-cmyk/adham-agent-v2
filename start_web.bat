@echo off
chcp 65001 >nul
title Adham Agent - Web Platform & Store
color 0A
cd /d "%~dp0"

if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
    goto :RUN
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
    goto :RUN
)

echo [ERROR] Python not found!
pause
exit /b 1

:RUN
echo ==============================================================================
echo Starting Enterprise Web Platform on http://127.0.0.1:8080...
echo ==============================================================================
"%PYTHON_EXE%" run_web_platform.py
pause
