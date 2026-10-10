@echo off
REM ============================================================
REM  安装/初始化 Appium 2 环境 (Windows)
REM  前提: Node.js 18+ (winget install OpenJS.NodeJS.LTS)
REM  说明: 国内网络慢时先执行  npm config set registry https://registry.npmmirror.com
REM        本脚本会安装 Android 驱动 uiautomator2; iOS 的 xcuitest 仅 macOS 需要
REM ============================================================
echo [1] 检查 Node.js ...
where node >nul 2>nul
if errorlevel 1 (
  echo     未安装 Node, 尝试用 winget 安装 LTS 版 ...
  winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
  echo     安装完 Node 后请重新打开终端再运行本脚本
  pause & exit /b 1
)
node -v
call npm --version

echo [2] 安装 Appium 2 (全局) ...
call npm install -g appium
if errorlevel 1 (
  echo [错误] appium 安装失败。若网络慢, 先执行: npm config set registry https://registry.npmmirror.com
  pause & exit /b 1
)

echo [3] 安装 Android 驱动 uiautomator2 ...
call appium driver install uiautomator2

echo [4] 安装 iOS 驱动 xcuitest ^(仅 macOS 需要; Windows 上失败可忽略, 不影响 Android^) ...
call appium driver install xcuitest 2>nul

echo.
echo [完成] 环境就绪, 验证结果:
appium --version
appium driver list --installed
echo.
echo 启动 Server: scripts\start_appium.bat
pause
