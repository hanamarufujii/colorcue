#!/bin/bash
# ColorCue を起動する（macOS）
cd "$(dirname "$0")" || exit 1
PORT=8777

lsof -ti tcp:$PORT | xargs kill 2>/dev/null
sleep 1

python3 bridge.py &
sleep 1

open -a "Google Chrome" "http://localhost:$PORT/index.html" 2>/dev/null \
  || open "http://localhost:$PORT/index.html"

echo "起動しました。このウィンドウは開いたままにしてください。"
echo "止めるときは Control-C。"
wait
