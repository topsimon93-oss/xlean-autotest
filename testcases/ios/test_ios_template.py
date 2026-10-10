"""iOS 模板用例(示例骨架)。

注意: iOS 自动化需 macOS + Xcode + Appium XCUITest driver;
      Windows 上运行会被 conftest 自动 skip, 不会报错。

接入真实 App 的 3 步:
  1. 改 config/local.yaml 的 ios.bundle_id 为你的 App;
  2. 在 pages/ 下新建页面对象, 定位符用 XCUITest 支持的策略:
       - ACCESSIBILITY_ID (最常用, 对应 label/accessibility)
       - IOS_PREDICATE    (如 AppiumBy.IOS_PREDICATE, "label BEGINSWITH '设置'")
       - XPATH / CLASS_CHAIN
  3. 在本目录新建 test_xxx.py, pytestmark 标 ios。
"""
from __future__ import annotations

import allure
import pytest
from appium.webdriver.common.appiumby import AppiumBy

from common.base_page import BasePage

pytestmark = [pytest.mark.ios, pytest.mark.demo]

# 模板: 以 iOS 系统"设置"App 为例(bundle_id: com.apple.Preferences)
SETTING_PAGE = {
    "ios": (AppiumBy.ACCESSIBILITY_ID, "设置"),
}


class _SettingsPage(BasePage):
    _search = {"ios": ("aid=搜索")}   # 替换为实际元素


@allure.title("[模板] iOS 启动并截图")
def test_ios_launch_template(driver, settle_seconds):
    import time
    time.sleep(settle_seconds)
    assert driver.page_source, "iOS 页面为空"
    allure.attach(driver.page_source, name="ios_page_source",
                  attachment_type=allure.attachment_type.XML)
