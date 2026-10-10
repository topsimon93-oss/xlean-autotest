@echo off
rem ============================================================
rem  xLean test console - double click to start
rem  starts local service 127.0.0.1:8123 and opens the page
rem  keep this window open; closing it stops the service
rem ============================================================
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] venv not found. Run scripts\setup_env.bat first.
  pause
  exit /b 1
)

echo [xLean Console] starting at http://127.0.0.1:8123 ...
"%PY%" ¿ØÖÆÌ¨_server.py
pause
