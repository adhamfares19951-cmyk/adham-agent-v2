@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ===== Ollama local model setup =====
where ollama >nul 2>&1
if errorlevel 1 (
  echo [ERROR] ollama command not found. Install Ollama first, then run this again.
  pause
  exit /b 1
)
echo.
echo Free disk space on this drive:
powershell -NoProfile -Command "Get-PSDrive -Name ((Get-Location).Drive.Name) | ForEach-Object { '{0:N1} GB free' -f ($_.Free/1GB) }"
echo.
echo Installed models:
ollama list
echo.
set "MODEL=qwen2.5:7b"
set /p MODEL=Model to use (Enter = qwen2.5:7b, or type e.g. qwen3:30b-a3b): 
if "%MODEL%"=="" set "MODEL=qwen2.5:7b"
echo.
echo Setting recommended Ollama variables for this user (context 8192, keep model loaded)...
setx OLLAMA_CONTEXT_LENGTH 8192 >nul
setx OLLAMA_KEEP_ALIVE -1 >nul
echo.
echo Pulling %MODEL% (skipped quickly if already installed)...
ollama pull %MODEL%
if errorlevel 1 (
  echo [ERROR] pull failed.
  pause
  exit /b 1
)
echo.
echo Benchmark (Arabic summary task) ...
> bench_prompt.txt echo لخّص بجملتين: اجتماع الفريق تأجل إلى الخميس الساعة العاشرة صباحاً، وسيناقش ميزانية الإعلانات الجديدة وخطة الإطلاق، ويجب تجهيز التقرير المالي قبله.
ollama run %MODEL% --verbose < bench_prompt.txt > ollama_bench.txt 2>&1
del /q bench_prompt.txt >nul 2>&1
type ollama_bench.txt
echo.
echo ================================================================
echo Done. Output also saved in ollama_bench.txt - tell Claude to read it.
echo To make the bot use it, add these two lines to .env (Notepad):
echo     OLLAMA_MODEL=%MODEL%
echo     LOCAL_FIRST=1
echo Then restart ollama (quit from tray, open again) and run run_clean.bat.
echo ================================================================
pause
