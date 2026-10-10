"""Demo 示例: Android 系统计算器, 演示 PageObject 标准用法。

需要: 设备上装有计算器, 且 config/local.yaml 的 android.app_package/app_activity
指向它(AOSP 镜像为 com.android.calculator2; Google Play 镜像为
com.google.android.calculator, 可先自行核对资源 id)。
运行: python -m pytest --platform android --with-demo
"""
from __future__ import annotations

import allure
import pytest

from pages.android_calculator_page import CalculatorPage

pytestmark = [pytest.mark.android, pytest.mark.demo]


@pytest.fixture
def calc(driver):
    page = CalculatorPage(driver)
    page.clear()          # 清屏, 保证起点干净
    return page


@allure.title("加法: 5 + 6 = 11")
def test_addition(calc):
    calc.tap_key("5+6=")
    assert calc.result_value() == "11", f"实际结果为: {calc.result_value()!r}"


@allure.title("连续输入与清屏")
def test_clear_works(calc):
    calc.tap_key("987")
    calc.tap_key("c")
    assert calc.is_display_empty(), "清屏后表达式区应为空"
