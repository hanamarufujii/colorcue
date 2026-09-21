#!/bin/bash
# ColorCue の自動起動を解除する
PLIST="$HOME/Library/LaunchAgents/jp.u-ma.colorcue.plist"
if [ -f "$PLIST" ]; then
  launchctl bootout "gui/$UID/jp.u-ma.colorcue" 2>/dev/null
  launchctl unload "$PLIST" 2>/dev/null
  rm -f "$PLIST"
  echo "自動起動をやめました。"
else
  echo "自動起動は登録されていません。"
fi
lsof -ti tcp:8777 2>/dev/null | xargs kill 2>/dev/null
echo "ColorCue も止めました。"
sleep 2
