@echo off
REM ============================================================
REM  启动 Android 模拟器 (Windows)
REM  用法: scripts\start_emulator.bat [AVD名称] [额外 emulator 参数...]
REM  默认 AVD: Pixel_7_Fresh; 查看全部: emulator -list-avds
REM
REM  加速问题(WHPX 崩溃/卡 offline, 常见于虚拟机/嵌套虚拟化):
REM    scripts\start_emulator.bat <AVD> -accel off -gpu guest -no-snapshot -cores 4
REM ============================================================
setlocal
set "AVD=%~1"
if "%AVD%"=="" set "AVD=Pixel_7_Fresh"

REM 收集 AVD 之后的额外参数原样透传给 emulator
set "EXTRA="
:args
shift
if "%~1"=="" goto :launch
set "EXTRA=%EXTRA% %~1"
goto :args

:launch
REM 定位 emulator: PATH 优先, 其次常见 SDK 路径
where emulator >nul 2>nul
if %errorlevel%==0 (
  set "EMU=emulator"
) else (
  if defined ANDROID_HOME (
    set "EMU=%ANDROID_HOME%\emulator\emulator.exe"
  ) else (
    set "EMU=%LOCALAPPDATA%\Android\Sdk\emulator\emulator.exe"
  )
  if not exist "%EMU%" (
    echo [错误] 找不到 emulator.exe, 请确认 Android SDK 已安装
    pause & exit /b 1
  )
)

echo 启动模拟器 [%AVD%] ... (WHPX 加速正常约 1~3 分钟; 若用 -accel off 纯软件模拟需 10~25 分钟)
"%EMU%" -avd "%AVD%" %EXTRA%
