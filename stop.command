#!/bin/bash
# ColorCue を止める（macOS）
PORT=8777
PIDS=$(lsof -ti tcp:$PORT 2>/dev/null)
if [ -z "$PIDS" ]; then
  echo "ColorCue は動いていません。"
else
  echo "$PIDS" | xargs kill 2>/dev/null
  sleep 1
  echo "ColorCue を止めました。"
fi
sleep 2
