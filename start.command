#!/bin/bash
# ColorCue を起動する（macOS）
# ターミナルから切り離して動かすので、このウィンドウは閉じて構いません。
cd "$(dirname "$0")" || exit 1
PORT=8777
LOG="$(pwd)/colorcue.log"

if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
  echo "ColorCue はすでに動いています。"
else
  nohup python3 bridge.py >> "$LOG" 2>&1 &
  disown
  sleep 1
  echo "ColorCue を起動しました。"
fi

open -a "Google Chrome" "http://localhost:$PORT/index.html" 2>/dev/null \
  || open "http://localhost:$PORT/index.html"

echo
echo "このウィンドウは閉じて構いません。ColorCue は動き続けます。"
echo "止めるときは stop.command をダブルクリックしてください。"
echo "記録は colorcue.log に残ります。"
sleep 2
