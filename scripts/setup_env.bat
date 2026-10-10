@echo off
REM ============================================================
REM  AppAutoTest 一键初始化 (Windows)
REM  用法: scripts\setup_env.bat
REM  步骤: 找 Python -> 建 .venv -> 装依赖 -> 生成 local.yaml -> 检查 Appium
REM ============================================================
setlocal
cd /d "%~dp0.."

REM ---------- 1. 找 Python (py launcher 优先, 其次 PATH) ----------
echo [1/5] 探测 Python ...
set "PYTHON_CMD="
where py >nul 2>nul
if %errorlevel%==0 (
  for /f "delims=" %%i in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do set "PYTHON_CMD=%%i"
)
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 for /f "delims=" %%i in ('python -c "import sys;print(sys.executable)"') do set "PYTHON_CMD=%%i"
)
if not defined PYTHON_CMD (
  echo [错误] 未找到 Python。请安装 Python 3.9+ 并勾选 "Add to PATH",
  echo        或执行: winget install Python.Python.3.12
  pause & exit /b 1
)
echo     使用 Python: %PYTHON_CMD%

REM ---------- 2. 创建 .venv ----------
echo [2/5] 创建虚拟环境 .venv ...
if not exist ".venv\Scripts\python.exe" "%PYTHON_CMD%" -m venv .venv
if not exist ".venv\Scripts\python.exe" (
  echo [错误] 创建虚拟环境失败
  pause & exit /b 1
)
set "VENV_PY=.venv\Scripts\python.exe"

REM ---------- 3. 升级 pip + 装依赖 ----------
echo [3/5] 升级 pip 并安装依赖 ...
"%VENV_PY%" -m pip install -U pip -q
"%VENV_PY%" -m pip install -r requirements.txt

REM ---------- 4. 生成个人配置(若不存在) ----------
echo [4/5] 检查 config\local.yaml ...
if not exist "config\local.yaml" (
  copy /Y "config\local.yaml.example" "config\local.yaml" >nul
  echo     已生成 config\local.yaml (个人私有配置, 已被 git 忽略)
)

REM ---------- 5. 环境检查汇总 ----------
echo [5/5] 环境检查汇总 ...
"%VENV_PY%" --version
where appium >nul 2>nul
if %errorlevel%==0 (
  echo     Appium: 已安装 & appium --version
) else (
  echo     [提示] 未检测到 Appium CLI, 请运行 scripts\appium_install.bat 安装
)

echo.
echo ============================================================
echo  初始化完成! 后续使用:
echo    scripts\run_tests.bat android ^<apk路径^>   ^(通用冒烟^)
echo    scripts\run_tests.bat demo                ^(加跑示例^)
echo    scripts\allure_report.bat                 ^(打开 Allure 报告^)
echo  需要先保证: 设备在线(adb devices) + Appium Server 在跑(start_appium.bat)
echo ============================================================
pause
