#!/usr/bin/env bash
# 生成并打开 Allure 报告 (Git Bash / Linux / macOS)
set -e
cd "$(dirname "$0")/.."

if ! command -v allure >/dev/null 2>&1; then
  echo "[提示] 未安装 allure, 可执行: brew install allure"
  exit 1
fi
allure generate allure-results -o reports/allure-report --clean
allure open reports/allure-report
