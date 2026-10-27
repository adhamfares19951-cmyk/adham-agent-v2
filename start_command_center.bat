@echo off
title Adham Agent Command Center Hub
cd /d "C:\Projects\adham-agent"
set PYTHONPATH=C:\Projects\adham-agent
call venv\Scripts\activate.bat
echo Starting Command Center on port 8080...
python run_command_center.py
pause
