@echo off
rem ColorCue を起動する（Windows）
cd /d "%~dp0"

start "" http://localhost:8777/index.html
python bridge.py

echo.
echo 終了しました。このウィンドウは閉じて構いません。
pause
