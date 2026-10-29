@echo off
cd /d C:\Projects\adham-agent
echo Running read-only tool audit (nothing is sent or changed)...
venv\Scripts\python.exe tool_audit.py
echo.
echo Report saved: C:\Projects\adham-agent\tool_audit_report.md
pause
