"""日志: 控制台 INFO + 文件 DEBUG(滚动)。文件输出到 logs/autotest.log。"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from common.config import ROOT

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logger(name: str = "autotest") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:          # 已初始化, 直接复用
        return logger
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    log_dir = ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_h = RotatingFileHandler(log_dir / "autotest.log", maxBytes=5 * 1024 * 1024,
                                 backupCount=5, encoding="utf-8")
    file_h.setLevel(logging.DEBUG)
    file_h.setFormatter(fmt)
    logger.addHandler(file_h)
    return logger


logger = setup_logger()
