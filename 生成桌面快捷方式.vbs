' Generate desktop shortcuts (double-click once, then delete this file)
Option Explicit
Dim ws, desk, lnk

Set ws = WScript.CreateObject("WScript.Shell")
desk = ws.SpecialFolders("Desktop")

Set lnk = ws.CreateShortcut(desk & "\“ªº¸≤‚ ‘xLean.lnk")
lnk.TargetPath = "C:\Users\xlean\WorkBuddy\2026-09-02-13-57-28\AppAutoTest\“ªº¸≤‚ ‘xLean.bat"
lnk.WorkingDirectory = "C:\Users\xlean\WorkBuddy\2026-09-02-13-57-28\AppAutoTest"
lnk.IconLocation = "C:\Windows\System32\shell32.dll,137"
lnk.Save

Set lnk = ws.CreateShortcut(desk & "\≤‚ ‘øÿ÷∆Ã®.lnk")
lnk.TargetPath = "C:\Users\xlean\WorkBuddy\2026-09-02-13-57-28\AppAutoTest\≤‚ ‘øÿ÷∆Ã®.bat"
lnk.WorkingDirectory = "C:\Users\xlean\WorkBuddy\2026-09-02-13-57-28\AppAutoTest"
lnk.IconLocation = "C:\Windows\System32\shell32.dll,220"
lnk.Save

WScript.Echo "OK: 2 shortcuts created on Desktop"
