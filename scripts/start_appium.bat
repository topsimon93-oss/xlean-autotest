@echo off
REM ============================================================
REM  启动 Appium Server (前台, Ctrl+C 停止)
REM  Appium 2 默认根路径即为 /, 无需 --base-path
REM ============================================================
cd /d "%~dp0.."

REM 优先用 PATH 上的 appium; 找不到时尝试常见全局安装位置
where appium >nul 2>nul
if %errorlevel%==0 (
  echo [Appium] 使用: appium
) else (
  if exist "%APPDATA%\npm\appium.cmd" (
    set "APPIUM=%APPDATA%\npm\appium.cmd"
    echo [Appium] 使用: %APPIUM%
  ) else (
    echo [错误] 未找到 appium 命令。
    echo   请先执行 scripts\appium_install.bat 完成安装 ^(需要 Node.js^), 
    echo   或临时使用: npx appium --address 127.0.0.1 --port 4723
    pause & exit /b 1
  )
)

echo 启动 Appium Server: http://127.0.0.1:4723   (Ctrl+C 停止)
if defined APPIUM (
  "%APPIUM%" server --address 127.0.0.1 --port 4723
) else (
  appium server --address 127.0.0.1 --port 4723
)
