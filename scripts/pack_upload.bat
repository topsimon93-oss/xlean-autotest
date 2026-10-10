@echo off
rem ============================================================
rem  xLean 自动化测试项目 — 一键打包成交付包
rem  用法: scripts\pack_upload.bat
rem  产出: 项目根目录下的 xlean-autotest-<日期>.zip
rem  排除: .venv / 截图 / 报告 / allure 结果 / 个人配置 / 大文件
rem ============================================================
setlocal
cd /d "%~dp0.."

set "STAMP=%date:~0,4%%date:~5,2%%date:~8,2%"
set "OUT=xlean-autotest-%STAMP%.zip"

echo.
echo  ============================================
echo   打包 xLean 自动化测试交付包
echo  ============================================
echo.

rem 先确认 zip 能力：优先 7z，其次 PowerShell 自带 Compress-Archive
where 7z >nul 2>nul
if %errorlevel%==0 (
    echo  [打包] 使用 7z ...
    7z a -tzip "%OUT%" ^
        run_full_pipeline.py conftest.py pytest.ini requirements.txt ^
        README.md ^
        testcases common pages config docs scripts ^
        一键测试xLean.bat start_appium.ps1 ^
        -xr!__pycache__ -xr!*.pyc -xr!.venv -xr!allure-results* ^
        -xr!reports -xr!screenshots -xr!logs -xr!config\local.yaml ^
        >nul
) else (
    echo  [打包] 使用 PowerShell Compress-Archive ...
    powershell -NoProfile -Command ^
      "$src=@('run_full_pipeline.py','conftest.py','pytest.ini','requirements.txt','README.md','testcases','common','pages','config','docs','scripts','一键测试xLean.bat','start_appium.ps1');" ^
      "$tmp=Join-Path $env:TEMP 'xlean-pack';" ^
      "Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue; New-Item $tmp -ItemType Directory | Out-Null;" ^
      "Copy-Item $src -Destination $tmp -Recurse;" ^
      "Remove-Item (Join-Path $tmp 'config\local.yaml') -Force -ErrorAction SilentlyContinue;" ^
      "Get-ChildItem $tmp -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force;" ^
      "Get-ChildItem $tmp -Recurse -Filter *.pyc | Remove-Item -Force;" ^
      "Compress-Archive -Path (Join-Path $tmp '*') -DestinationPath '$OUT' -Force;" ^
      "Remove-Item $tmp -Recurse -Force"
)

if not exist "%OUT%" (
    echo.
    echo  [错误] 打包失败，未生成 %OUT%
    pause
    exit /b 1
)

echo.
echo  ============================================
echo  打包完成！
echo  文件: %cd%\%OUT%
echo  ============================================
echo.
echo  下一步（推上云给伙伴用）：
echo    1. 上传这个 zip 到 git / 网盘 / 公司文档库
echo    2. 伙伴下载解压，看 docs\团队接入指南.md
echo    3. 跑 scripts\setup_env.bat + appium_install.bat 即可上手
echo.
pause
