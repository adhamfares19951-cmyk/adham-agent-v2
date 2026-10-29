@echo off
cd /d C:\Projects\adham-agent
echo A browser window will open. Sign in with the YouTube channel account and press Allow.
venv\Scripts\python.exe -c "from tools.youtube_publisher import run_oauth_flow_interactive as r; print(r())"
echo.
pause
