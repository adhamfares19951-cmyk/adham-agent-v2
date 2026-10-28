@echo off
chcp 65001 >nul
title Right Hand Bot (Adham Agent)
cd /d "%~dp0"

echo [توجيه] المشغل الرسمي المعتمد للبوت هو: start_watchdog.bat
if exist "%~dp0bot.lock" (
    echo [تحذير] البوت يعمل بالفعل أو ملف bot.lock موجود!
)
call start_bot.bat
