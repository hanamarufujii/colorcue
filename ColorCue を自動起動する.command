#!/bin/bash
# Macを起動したとき、ColorCue が勝手に立ち上がるようにする（ログイン項目に登録）
cd "$(dirname "$0")" || exit 1
PLIST="$HOME/Library/LaunchAgents/jp.u-ma.colorcue.plist"
DIR="$(pwd)"

# 古いブリッジが 8777 を掴んだままだと新しいものが起動できないので、先に止める
lsof -ti tcp:8777 2>/dev/null | xargs kill 2>/dev/null
sleep 1

mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>jp.u-ma.colorcue</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$DIR/bridge.py</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$DIR/colorcue.log</string>
  <key>StandardErrorPath</key><string>$DIR/colorcue.log</string>
</dict>
</plist>
PL

launchctl bootout "gui/$UID/jp.u-ma.colorcue" 2>/dev/null
launchctl unload "$PLIST" 2>/dev/null
launchctl bootstrap "gui/$UID" "$PLIST" 2>/dev/null || launchctl load "$PLIST" 2>/dev/null
sleep 2

if lsof -nP -iTCP:8777 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "自動起動を登録しました。ColorCue は今も動いています。"
  echo "これから Mac を起動するたびに、自動で立ち上がります。"
else
  echo "登録しましたが、まだ立ち上がっていません。colorcue.log を見てください。"
fi
echo
echo "やめたいときは「自動起動をやめる.command」をダブルクリックしてください。"
sleep 3
