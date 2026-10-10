# -*- coding: utf-8 -*-
"""重写 测试控制台.bat 为纯 ASCII（cmd 按 GBK 解析 bat，中文内容会撕碎命令）。"""
from pathlib import Path

lines = [
    "@echo off",
    "rem ============================================================",
    "rem  xLean test console - double click to start",
    "rem  starts local service 127.0.0.1:8123 and opens the page",
    "rem  keep this window open; closing it stops the service",
    "rem ============================================================",
    'cd /d "%~dp0"',
    "",
    'set "PY=.venv\\Scripts\\python.exe"',
    'if not exist "%PY%" (',
    "  echo [ERROR] venv not found. Run scripts\\setup_env.bat first.",
    "  pause",
    "  exit /b 1",
    ")",
    "",
    'echo [xLean Console] starting at http://127.0.0.1:8123 ...',
    '"%PY%" 控制台_server.py',
    "pause",
]

p = Path(__file__).resolve().parent.parent / "测试控制台.bat"
p.write_bytes(("\r\n".join(lines) + "\r\n").encode("gbk"))
print("已重写为 GBK；中文仅剩 server.py 文件名（GBK 下 cmd 能正确解析）")
