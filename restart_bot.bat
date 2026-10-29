@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PY=%~dp0venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
echo Stopping old adham-agent processes...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and ($_.CommandLine -like '*adham-agent*' -or $_.CommandLine -like '*watchdog.py*' -or $_.CommandLine -like '*run_agency_os.py*') } | ForEach-Object { Write-Host ('stopping PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }"
if exist bot.lock del /f /q bot.lock
timeout /t 2 >nul
"%PY%" -m py_compile main.py brain.py llm.py config.py tools\__init__.py tools\workspace_coder.py tools\skills_engine.py tools\jobs.py
if errorlevel 1 (echo [ERROR] Syntax check failed. Bot NOT started. & pause & exit /b 1)
echo Starting the bot (data is kept)...
"%PY%" watchdog.py
pause
