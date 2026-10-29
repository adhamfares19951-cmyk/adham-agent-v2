@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [0/3] Stopping any old adham-agent processes (old code may still be running)...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'python*' -and ($_.CommandLine -like '*adham-agent*' -or $_.CommandLine -like '*watchdog.py*' -or $_.CommandLine -like '*run_agency_os.py*') } | ForEach-Object { Write-Host ('stopping PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force }"
if exist bot.lock (
  for /f "usebackq delims=" %%P in ("bot.lock") do taskkill /F /PID %%P >nul 2>&1
  del /f /q bot.lock >nul 2>&1
)
timeout /t 2 >nul
echo [1/3] Clearing reminders and pending approvals (DB backup is created first)...
if exist "%~dp0venv\Scripts\python.exe" (set "PY=%~dp0venv\Scripts\python.exe") else (set "PY=python")
"%PY%" reset_test_data.py
echo.
echo [2/3] Syntax check of core files...
"%PY%" -m py_compile main.py brain.py llm.py config.py tools\__init__.py tools\workspace_coder.py tools\skills_engine.py
if errorlevel 1 (
  echo [ERROR] Syntax check failed. Bot NOT started.
  pause
  exit /b 1
)
echo [3/3] OK. Starting the bot...
call start_watchdog.bat
