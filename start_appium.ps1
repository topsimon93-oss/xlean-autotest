# ============================================================
# Appium Server 一键启动
# 用受管 Node 运行工作区里的 Appium，驱动读 ~/.appium（uiautomator2 已装好）
#
# 用法（PowerShell）：
#   .\start_appium.ps1          # 前台启动，Ctrl+C 停止
# ============================================================

$node = "C:\Users\xlean\.workbuddy\binaries\node\versions\22.22.2-6\node.exe"
$appiumMain = "C:\Users\xlean\.workbuddy\binaries\node\workspace\node_modules\appium\build\lib\main.js"

if (-not (Test-Path $appiumMain)) {
    Write-Host "[错误] 找不到 appium: $appiumMain"
    Write-Host "       先安装: cd C:\Users\xlean\.workbuddy\binaries\node\workspace; npm install appium"
    exit 1
}

Write-Host "[启动] Appium Server @ http://127.0.0.1:4723 （Ctrl+C 停止）"
$env:APPIUM_HOME = "C:\Users\xlean\.appium"
& $node $appiumMain --port 4723 --address 127.0.0.1 --log-level info
