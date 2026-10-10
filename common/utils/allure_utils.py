"""Allure 辅助: 截图附件、文本附件、步骤装饰器、时间戳。"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import allure


def ts(prefix: str = "") -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"


def safe_name(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name).strip("_") or "file"


def attach_text(title: str, content: str) -> None:
    allure.attach(str(content), name=title, attachment_type=allure.attachment_type.TEXT)


def attach_screenshot(driver, name: str = "screenshot", directory: Path | None = None) -> Path | None:
    """截图存盘并挂到 Allure。失败不阻断用例, 返回 None。"""
    from common.config import config
    directory = directory or config.screenshots_dir
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{safe_name(name)}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.png"
    try:
        ok = driver.save_screenshot(str(path))
        if ok and path.exists():
            allure.attach.file(str(path), name=safe_name(name),
                               attachment_type=allure.attachment_type.PNG)
            return path
    except Exception:  # noqa: BLE001
        pass
    return None


def step(title: str):
    """把普通方法包装为 Allure 步骤: @step('点击登录') 用法同 allure.step。"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with allure.step(title):
                return func(*args, **kwargs)
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator
