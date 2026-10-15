@echo off
chcp 65001 >nul
title Right Hand Bot (Adham Agent)
color 0B
cd /d "%~dp0"

if exist "%~dp0python_runtime\python.exe" (
    set "PYTHON_EXE=%~dp0python_runtime\python.exe"
    goto :RUN
)

if exist "%~dp0venv\Scripts\python.exe" (
    set "PYTHON_EXE=%~dp0venv\Scripts\python.exe"
    goto :RUN
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=python"
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
echo Starting Right Hand Bot... (close this window or press Ctrl+C to stop)
"%PYTHON_EXE%" main.py
echo.
echo The bot stopped. Read the message above, then press any key to close.
pause >nul
