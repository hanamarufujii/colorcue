#!/usr/bin/env python3
"""
ColorCue — ローカルブリッジ

・このフォルダを http://localhost:8777 で配信する
・POST /send {"text": "...", "app": "アプリ名"} … そのアプリを手前に出して貼り付けて Enter
                                              app を省くと、いま手前のアプリへ
・POST /return                … Enter だけ送る
・GET  /apps                  … 起動中のアプリ名の一覧（送り先を選ぶため）

macOS  : osascript（System Events）でキーを送る
Windows: PowerShell の SendKeys でキーを送る

外部には一切つながない。待ち受けは 127.0.0.1 のみ。
"""

import http.server
import json
import os
import socketserver
import subprocess
import sys
import tempfile
import time

PORT = 8777
DIR = os.path.dirname(os.path.abspath(__file__))

IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")

# ---------------------------------------------------------------- キー送信

AS_RETURN = 'tell application "System Events" to keystroke return'
AS_PASTE = 'tell application "System Events" to keystroke "v" using command down'

PS_HEAD = "Add-Type -AssemblyName System.Windows.Forms; "
PS_RETURN = PS_HEAD + "[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')"
PS_PASTE = PS_HEAD + "[System.Windows.Forms.SendKeys]::SendWait('^v')"


def _run(cmd):
    subprocess.run(cmd, check=True, capture_output=True, timeout=45)


def _ps(script):
    _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script])


def press_return():
    if IS_MAC:
        _run(["osascript", "-e", AS_RETURN])
    elif IS_WIN:
        _ps(PS_RETURN)
    else:
        raise RuntimeError("このOSには対応していません（macOS / Windows のみ）")


def list_apps():
    """画面に出ているアプリの名前を返す。"""
    if IS_MAC:
        script = ('tell application "System Events" to get name of every process '
                  'whose background only is false')
        r = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
        names = r.stdout.decode("utf-8", "replace").strip()
        return sorted({n.strip() for n in names.split(",") if n.strip()})
    if IS_WIN:
        script = ("Get-Process | Where-Object {$_.MainWindowTitle -ne ''} "
                  "| Select-Object -ExpandProperty ProcessName")
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, timeout=15,
        )
        names = r.stdout.decode("utf-8", "replace").splitlines()
        return sorted({n.strip() for n in names if n.strip()})
    return []


def activate(app):
    """指定したアプリを手前に出す。"""
    if not app:
        return
    if IS_MAC:
        _run(["osascript", "-e", f'tell application "{app}" to activate'])
    elif IS_WIN:
        _ps("Add-Type -AssemblyName Microsoft.VisualBasic; "
            f"[Microsoft.VisualBasic.Interaction]::AppActivate('{app}')")
    time.sleep(0.35)   # 手前に出てくるのを待つ


def press_paste():
    if IS_MAC:
        _run(["osascript", "-e", AS_PASTE])
    elif IS_WIN:
        _ps(PS_PASTE)
    else:
        raise RuntimeError("このOSには対応していません（macOS / Windows のみ）")


# ---------------------------------------------------------------- クリップボード

def clipboard_get():
    if IS_MAC:
        return subprocess.run(["pbpaste"], capture_output=True, timeout=5).stdout.decode("utf-8", "replace")
    if IS_WIN:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", "Get-Clipboard -Raw"],
            capture_output=True, timeout=10,
        )
        return r.stdout.decode("utf-8", "replace")
    return ""


def clipboard_set(text):
    if IS_MAC:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), timeout=5)
        return
    if IS_WIN:
        # 日本語をそのまま渡すため、UTF-8 のファイル経由にする
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            _ps(f"Get-Content -Raw -Encoding UTF8 '{path}' | Set-Clipboard")
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass


def paste_and_return(text, app=None):
    """app（省略時は最前面）に text を貼り付けて Enter。クリップボードは元へ戻す。"""
    saved = clipboard_get()
    try:
        clipboard_set(text)
        activate(app)
        time.sleep(0.05)
        press_paste()
        time.sleep(0.15)      # 貼り付けが反映されるのを待つ
        press_return()
    finally:
        time.sleep(0.2)
        clipboard_set(saved)


# ---------------------------------------------------------------- サーバー

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_POST(self):
        route = self.path.rstrip("/")
        if route not in ("/return", "/send"):
            self.send_error(404)
            return

        text, app = "", None
        if route == "/send":
            try:
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n) or b"{}")
                text = (body.get("text") or "").strip()
                app = (body.get("app") or "").strip() or None
            except Exception:
                text, app = "", None

        try:
            if route == "/send" and text:
                paste_and_return(text, app)
            else:
                press_return()
            payload = {"ok": True}
        except subprocess.CalledProcessError as e:
            payload = {"ok": False, "error": e.stderr.decode("utf-8", "replace").strip()}
        except Exception as e:
            payload = {"ok": False, "error": str(e)}

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

        if not payload["ok"]:
            print("送信に失敗:", payload["error"], file=sys.stderr, flush=True)

    def do_GET(self):
        if self.path.rstrip("/") == "/apps":
            try:
                payload = {"ok": True, "apps": list_apps()}
            except Exception as e:
                payload = {"ok": False, "error": str(e), "apps": []}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    if not (IS_MAC or IS_WIN):
        sys.exit("ColorCue は macOS と Windows にだけ対応しています。")
    with Server(("127.0.0.1", PORT), Handler) as httpd:
        print(f"ColorCue 待ち受け中 → http://localhost:{PORT}/index.html")
        print("止めるときは Control-C。このウィンドウは開いたままにしてください。")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n終了しました。")
