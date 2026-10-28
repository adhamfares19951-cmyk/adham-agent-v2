@echo off
chcp 65001 >nul
title Right Hand Bot (Adham Agent)
color 0B
cd /d "%~dp0"

echo ========================================================
echo [ملاحظة] المشغل الأساسي والمعتمد للبوت هو: start_watchdog.bat
echo ========================================================

if exist "%~dp0bot.lock" (
    echo [تحذير] تم اكتشاف ملف bot.lock!
    echo قد يكون البوت يعمل بالفعل في نافذة أخرى أو عبر start_watchdog.bat.
    echo لتفادي أخطاء تضارب الرسائل (Conflict)، يرجى استخدام start_watchdog.bat أو إغلاق الجلسة الأخرى.
    echo.
)

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

echo [ERROR] No Python runtime found!
pause
exit /b 1

:RUN
echo Starting Right Hand Bot... (close this window or press Ctrl+C to stop)
"%PYTHON_EXE%" main.py
echo.
echo The bot stopped. Read the message above, then press any key to close.
pause >nul
