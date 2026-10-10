#!/usr/bin/env bash
# AppAutoTest 一键初始化 (Git Bash / Linux / macOS)
set -e
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
echo "[1/4] 创建虚拟环境 .venv"
"$PY" -m venv .venv
source .venv/bin/activate

echo "[2/4] 升级 pip"
python -m pip install -U pip -q

echo "[3/4] 安装依赖"
pip install -r requirements.txt

echo "[4/4] 检查 Appium"
if command -v appium >/dev/null 2>&1; then
  appium --version
else
  echo "[提示] 未检测到 Appium, 请执行: npm i -g appium && appium driver install uiautomator2"
fi

echo "完成! 常用:"
echo "  scripts/run_tests.sh android <apk>   # 通用冒烟"
echo "  scripts/allure_report.sh             # 打开报告"
