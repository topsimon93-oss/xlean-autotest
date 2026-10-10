@echo off
rem ============================================================
rem  xLean one-click test
rem  check device -> check/start appium -> run tests -> open report
rem ============================================================
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"

echo.
echo  ==============================================
echo    xLean 自动化测试 - 一键启动
echo  ==============================================
echo.

if not exist "%PY%" (
  echo  [错误] 没找到虚拟环境 .venv\Scripts\python.exe
  echo         请先运行 scripts\setup_env.bat 初始化环境
  pause
  exit /b 1
)

echo  [1/4] 检查手机连接...
set "DEV="
for /f "delims=" %%i in ('adb devices 2^>nul ^| findstr /r "device$"') do set "DEV=%%i"
if "%DEV%"=="" (
  echo.
  echo  [警告] 没检测到已授权的设备！
  echo         请：插 USB 线 -^> 手机点「允许 USB 调试」
  echo.
  adb devices
  echo.
  echo  插好线后按任意键重试，或直接关掉窗口。
  pause
  for /f "delims=" %%i in ('adb devices 2^>nul ^| findstr /r "device$"') do set "DEV=%%i"
  if "%DEV%"=="" exit /b 1
)
echo        设备已连接: %DEV%
echo.

echo  [2/4] 检查 Appium Server...
netstat -ano 2>nul | findstr ":4723" | findstr "LISTENING" >nul
if errorlevel 1 (
  echo        Appium 未运行，正在启动...
  start "Appium Server" powershell -NoProfile -ExecutionPolicy Bypass -File "start_appium.ps1"
  echo        等待 Appium 就绪...
  timeout /t 8 /nobreak >nul
) else (
  echo        Appium 已在运行
)
echo.

echo  [3/4] 开始跑测试（13 条用例，约 12-20 分钟）...
echo        手机屏幕会自动操作，请勿碰触！
echo.
"%PY%" run_full_pipeline.py --skip-artemis

echo.
echo  [4/4] 测试完成，打开报告...
start "" "reports\pipeline\pipeline_report.html"
echo.
echo  本次报告: reports\pipeline\pipeline_report.html
echo  历史趋势: reports\pipeline\trend.html
echo.
pause
