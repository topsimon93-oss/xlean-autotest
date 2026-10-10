#!/usr/bin/env bash
# AppAutoTest 一键运行 (Git Bash / Linux / macOS)
# 用法:
#   scripts/run_tests.sh                    # Android 通用冒烟
#   scripts/run_tests.sh android apps/a.apk
#   scripts/run_tests.sh ios
#   scripts/run_tests.sh android apps/a.apk demo
set -e
cd "$(dirname "$0")/.."

PY=".venv/bin/python"
[ -x "$PY" ] || { echo "[错误] 请先运行 scripts/setup_env.sh"; exit 1; }

PLAT="${1:-android}"
APP="${2:-}"
MODE="${3:-}"
shift 2>/dev/null || true

ARGS="--platform $PLAT"
[ -n "$APP" ] && ARGS="$ARGS --app $APP"
DEMO=""
[ "$MODE" = "demo" ] && DEMO="--with-demo"

echo "[AppAutoTest] python -m pytest $ARGS $DEMO $*"
"$PY" -m pytest $ARGS $DEMO "$@"
