@echo off
chcp 65001 > nul
title ربط قناة يوتيوب مع بوت أدهم
cd /d "%~dp0"

echo ==============================================================
echo     جارٍ فتح متصفحك لربط قناة يوتيوب مع البوت...
echo ==============================================================

if exist "python_runtime\python.exe" (
    "python_runtime\python.exe" setup_youtube.py
) else (
    python setup_youtube.py
)

pause
