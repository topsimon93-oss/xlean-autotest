# -*- coding: utf-8 -*-
"""重写 vbs 为 GBK 无 BOM（wscript 原生 ANSI 解析，避开 BOM 无效字符错误）。"""
from pathlib import Path

lines = [
    "' Generate desktop shortcuts (double-click once, then delete this file)",
    "Option Explicit",
    "Dim ws, desk, lnk",
    "",
    'Set ws = WScript.CreateObject("WScript.Shell")',
    'desk = ws.SpecialFolders("Desktop")',
    "",
    'Set lnk = ws.CreateShortcut(desk & "\\一键测试xLean.lnk")',
    'lnk.TargetPath = "C:\\Users\\xlean\\WorkBuddy\\2026-09-02-13-57-28\\AppAutoTest\\一键测试xLean.bat"',
    'lnk.WorkingDirectory = "C:\\Users\\xlean\\WorkBuddy\\2026-09-02-13-57-28\\AppAutoTest"',
    'lnk.IconLocation = "C:\\Windows\\System32\\shell32.dll,137"',
    "lnk.Save",
    "",
    'Set lnk = ws.CreateShortcut(desk & "\\测试控制台.lnk")',
    'lnk.TargetPath = "C:\\Users\\xlean\\WorkBuddy\\2026-09-02-13-57-28\\AppAutoTest\\测试控制台.bat"',
    'lnk.WorkingDirectory = "C:\\Users\\xlean\\WorkBuddy\\2026-09-02-13-57-28\\AppAutoTest"',
    'lnk.IconLocation = "C:\\Windows\\System32\\shell32.dll,220"',
    "lnk.Save",
    "",
    'WScript.Echo "OK: 2 shortcuts created on Desktop"',
]

p = Path(__file__).resolve().parent.parent / "生成桌面快捷方式.vbs"
p.write_bytes(("\r\n".join(lines) + "\r\n").encode("gbk"))
print("已重写为 GBK 无 BOM；前 3 字节:", p.read_bytes()[:3].hex())
