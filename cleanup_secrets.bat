@echo off
chcp 65001 >nul
echo This deletes the local safety copy of the old cookie files:
echo   C:\Projects\adham-agent-secrets-safe
echo Do this ONLY after you logged out of all Google/CJ sessions.
set /p OK=Type YES to delete: 
if /i not "%OK%"=="YES" (echo Cancelled. & pause & exit /b 0)
if exist "C:\Projects\adham-agent-secrets-safe" rmdir /s /q "C:\Projects\adham-agent-secrets-safe"
if exist "C:\Projects\adham-agent-secrets-safe" (echo Could not delete fully. Delete it manually.) else (echo Deleted.)
echo.
echo The git backup bundle (C:\Projects\adham-agent-backup-pre-filter.bundle) still contains the OLD history with the cookies.
echo Move it to an external drive or delete it when you are sure the clean repo works.
pause
