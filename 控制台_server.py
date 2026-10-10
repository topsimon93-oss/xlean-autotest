# -*- coding: utf-8 -*-
"""xLean 测试控制台 —— 本地小服务。

双击「测试控制台.bat」启动：起本地 HTTP 服务(8123)并自动打开控制台页面。
网页按钮通过 /api/* 真正执行 bat / 打开报告，绕开浏览器不能启动本地程序的限制。
"""
import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent
PORT = 8123
BAT_RUN = ROOT / "一键测试xLean.bat"
BAT_APPIUM = ROOT / "scripts" / "start_appium.bat"
PAGE = ROOT / "控制台.html"
REPORT = ROOT / "reports" / "pipeline" / "pipeline_report.html"
TREND = ROOT / "reports" / "pipeline" / "trend.html"


def adb_devices() -> list[str]:
    try:
        out = subprocess.run(["adb", "devices"], capture_output=True, text=True,
                             timeout=10).stdout
        return [l for l in out.splitlines() if l.strip() and not l.startswith("List")]
    except Exception:
        return []


def appium_alive() -> bool:
    try:
        out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True,
                             timeout=10).stdout
        return any(":4723" in l and "LISTENING" in l.upper() for l in out.splitlines())
    except Exception:
        return False


def popen_bat(bat: Path):
    if not bat.exists():
        return False, f"找不到 {bat.name}"
    subprocess.Popen(["cmd", "/c", "start", "", str(bat)], cwd=str(ROOT))
    return True, f"已启动 {bat.name}（弹出了独立窗口）"


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif u.path == "/api/status":
            devs = adb_devices()
            ok_dev = any(l.strip().endswith("device") and ":" not in l.split()[0]
                         for l in devs)
            self._json({"dev_ok": ok_dev, "dev_lines": devs,
                        "appium_ok": appium_alive()})
        elif u.path == "/api/run":
            ok, msg = popen_bat(BAT_RUN)
            self._json({"ok": ok, "msg": msg})
        elif u.path == "/api/appium":
            ok, msg = popen_bat(BAT_APPIUM)
            self._json({"ok": ok, "msg": msg})
        elif u.path == "/api/open":
            t = parse_qs(u.query).get("t", [""])[0]
            target = REPORT if t == "report" else TREND
            if target.exists():
                os.startfile(str(target))  # noqa
                self._json({"ok": True})
            else:
                self._json({"ok": False, "msg": "报告还不存在，先跑一次测试"}, 404)
        else:
            self._json({"msg": "not found"}, 404)

    def log_message(self, *a):  # 静音访问日志
        pass


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"控制台服务已启动: http://127.0.0.1:{PORT}  (Ctrl+C 停止)")
    threading.Timer(0.8, lambda: os.startfile(f"http://127.0.0.1:{PORT}")).start()
    srv.serve_forever()
