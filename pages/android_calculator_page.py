"""示例 Page Object: AOSP 系统计算器(大多数 Android 模拟器镜像自带, 包名 com.android.calculator2)。

Demo 目的: 展示"双端定位符字典 + BasePage 封装"的标准写法。
真实被测 App 接入后, 把这里的定位符替换为业务元素即可。

用法:
    python -m pytest --platform android --with-demo testcases/android/
"""
from __future__ import annotations

import re

from appium.webdriver.common.appiumby import AppiumBy

from common.base_page import BasePage

_PKG = "com.android.calculator2"
_ID = f"{_PKG}:id"

# 操作符 -> 资源 id 后缀
_OPS = {
    "+": "op_add",
    "-": "op_sub",
    "*": "op_mul",
    "x": "op_mul",
    "/": "op_div",
    "=": "op_eq",
    ".": "op_pnt",
    "c": "op_clr",        # 清屏
    "del": "op_del",
}


class CalculatorPage(BasePage):
    # ---- 双端定位符示例(ios 部分为模板写法, 需按真机/模拟器实际元素调整) ----
    _formula = {
        "android": (AppiumBy.ID, f"{_ID}/formula"),
        "ios":     (AppiumBy.ACCESSIBILITY_ID, "formula"),
    }
    _result = {
        "android": (AppiumBy.ID, f"{_ID}/result"),
        "ios":     (AppiumBy.ACCESSIBILITY_ID, "result"),
    }

    def _digit(self, d: str):
        return {
            "android": (AppiumBy.ID, f"{_ID}/digit_{d}"),
            "ios":     (AppiumBy.ACCESSIBILITY_ID, d),
        }

    def _op(self, op: str):
        suffix = _OPS[op]
        return {
            "android": (AppiumBy.ID, f"{_ID}/{suffix}"),
            "ios":     (AppiumBy.ACCESSIBILITY_ID, suffix),
        }

    # ---------------- 业务动作 ----------------
    def tap_key(self, key: str) -> "CalculatorPage":
        """支持整串输入, 如 tap_key('5+6=') 会逐个按键点击。"""
        for ch in str(key):
            if ch in _OPS:
                self.click(self._op(ch), desc=f"按键 {ch}")
            elif ch.isdigit():
                self.click(self._digit(ch), desc=f"数字 {ch}")
            else:
                raise ValueError(f"不支持的按键: {ch}")
        return self

    def clear(self) -> "CalculatorPage":
        self.click(self._op("c"), desc="清屏")
        return self

    def display_text(self) -> str:
        """当前表达式区文本(如 5+6=)。"""
        try:
            return self.get_text(self._formula)
        except Exception:  # noqa: BLE001
            return ""

    def is_display_empty(self) -> bool:
        return self.display_text() == ""

    def result_value(self) -> str:
        """计算结果: 兼容 '11' 或 '5+6=' 多种显示形态, 取最后一个等号后的数字。"""
        text = f"{self.display_text()} {self.get_text(self._result)}"
        if "=" in text:
            tail = text.split("=")[-1]
        else:
            tail = text
        m = re.search(r"-?\d+(?:\.\d+)?", tail)
        return m.group(0) if m else ""
