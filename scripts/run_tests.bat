@echo off
REM ============================================================
REM  一键运行测试 (Windows)
REM  用法(参数顺序不限):
REM    scripts\run_tests.bat                          ^<== Android 通用冒烟(自动扫 apps\* 最新 apk^)
REM    scripts\run_tests.bat android apps\a.apk       ^<== 指定平台+App
REM    scripts\run_tests.bat demo                     ^<== 加跑 demo 示例
REM    scripts\run_tests.bat android apps\a.apk demo --udid=emulator-5554
REM  说明: android/ios/demo 为保留字, 其余参数原样透传给 pytest
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0.."

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [错误] 未找到虚拟环境, 请先运行 scripts\setup_env.bat
  exit /b 1
)

set "PLAT=android"
set "DEMO="
set "EXTRA="
for %%A in (%*) do (
  if /I "%%A"=="android"      ( set "PLAT=android" )
  else if /I "%%A"=="ios"     ( set "PLAT=ios" )
  else if /I "%%A"=="demo"    ( set "DEMO=--with-demo" )
  else                        ( set "EXTRA=!EXTRA! %%A" )
)

echo [AppAutoTest] %PY% -m pytest --platform %PLAT% %DEMO% %EXTRA%
"%PY%" -m pytest --platform %PLAT% %DEMO% %EXTRA%
