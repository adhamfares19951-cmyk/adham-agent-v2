@echo off
title TikTok Automation Setup - Core Trade AI
cd /d "%~dp0"
echo ========================================================
echo   Launching TikTok Interactive Authentication Setup...
echo ========================================================
python_runtime\python.exe setup_tiktok.py
pause
