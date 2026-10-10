@echo off
REM ============================================================
REM  生成并打开 Allure 报告 (Windows)
REM  用法: scripts\allure_report.bat
REM  前置: allure 命令行工具(可选 winget 安装) + Java
REM  本脚本会自动兜底 Java: 找不到 JAVA_HOME 时使用 Android Studio 自带 JBR
REM ============================================================
setlocal
cd /d "%~dp0.."

REM ---------- 1. 兜底 Java (Android Studio JBR) ----------
if not defined JAVA_HOME (
  if exist "C:\Program Files\Android\Android Studio\jbr" (
    set "JAVA_HOME=C:\Program Files\Android\Android Studio\jbr"
    echo [Java] 自动使用 Android Studio JBR: %JAVA_HOME%
  )
)

REM ---------- 2. 检查 allure CLI ----------
where allure >nul 2>nul
if errorlevel 1 (
  echo [提示] 未安装 Allure 命令行工具, 二选一安装后重跑:
  echo    A. winget install qameta.allure
  echo    B. scoop install allure
  echo  也可以直接浏览器打开已生成的旧报告: reports\allure-report\index.html
  pause & exit /b 1
)

REM ---------- 3. 生成 + 打开 ----------
echo [1/2] 生成报告 reports\allure-report ...
call allure generate allure-results -o reports\allure-report --clean
if errorlevel 1 (
  echo [错误] allure generate 失败, 常见原因: Java 不可用。请确认已装 Java 或本脚本的 JBR 兜底路径存在。
  pause & exit /b 1
)
echo [2/2] 打开报告 ...
call allure open reports\allure-report
