#!/usr/bin/env bash
# 启动 Appium Server (前台, Ctrl+C 停止)
cd "$(dirname "$0")/.."
appium server --address 127.0.0.1 --port 4723
