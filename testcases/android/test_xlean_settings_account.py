"""xLean 设备设置页 + 账号信息页 测试（教学示范，全部只读）。

覆盖:
  - 设备设置页: 能进入、三组标题在、10 个入口在、返回键能回首页
  - 账号信息页: 能进入、基本信息区在、邮箱格式合法、退出登录/注销账号按钮存在

安全约定: 不点 退出登录/注销账号/切换/设置密码/任何组内入口。
运行:
    python -m pytest testcases/android/test_xlean_settings_account.py --platform android -v
"""
from __future__ import annotations

import re

import allure
import pytest

from common.logger import logger
from common.utils.allure_utils import attach_screenshot
from pages.android_xlean_settings_page import (
    AccountInfoPage,
    DeviceSettingsPage,
    open_account_info,
    open_device_settings,
)
from pages.android_xlean_page import XLeanHomePage

pytestmark = [pytest.mark.android]

_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


@pytest.fixture
def home(driver) -> XLeanHomePage:
    """起点=「真·首页」(弹窗关掉、「进入设备」可见)。

    会话前已由 conftest 在 adb 层冷启动 App(会话内杀 App 会弄脏 uiautomator2
    连接, 之后 find 静默失败 —— 实测大坑), 这里只等首页就绪 + 关弹窗。

    坑位记录:
    1. 抽屉菜单里也有「xLean TR1」, 设备名可见不代表菜单收起 -> 用「进入设备」判断。
    2. 「重点区域AI推荐」「忽略推荐？」等弹窗会晚到 -> dismiss_popups() 只点安全按钮。
    """
    page = XLeanHomePage(driver)
    page.dismiss_popups()
    if not page.home_ready():
        page.wait_visible(page._enter_device, timeout=20)
        page.dismiss_popups()
    return page


# =========================================================================
# 设备设置页
# =========================================================================
@allure.title("设备设置页能打开，三组标题齐全")
def test_settings_page_opens(home):
    settings = open_device_settings(home)
    assert settings.page_title_visible(), "设备设置页标题未出现（没进去？）"
    assert settings.group_headers_visible(), "清洁设置/设备控制/设备管理 三组标题不全"
    attach_screenshot(settings.driver, "设备设置页")


@allure.title("设备设置页 10 个入口全部显示")
def test_settings_entries_present(home):
    settings = open_device_settings(home)
    missing = settings.missing_entries()
    attach_screenshot(settings.driver, "设备设置入口")
    assert not missing, f"以下入口未显示: {missing}"


@allure.title("设备设置页返回键能回首页")
def test_settings_back_to_home(home):
    settings = open_device_settings(home)
    assert settings.page_title_visible(), "设备设置页未打开"
    settings.back()
    # App V0.22.6.0 起首页无「xLean TR1」设备名, 改用「进入设备」入口判断返回成功
    assert home.home_ready(), "返回后首页未就绪（「进入设备」入口缺失）"


# =========================================================================
# 账号信息页（已登录态）
# =========================================================================
@allure.title("账号信息页能打开，基本信息区齐全")
def test_account_page_opens(home):
    acct = open_account_info(home)
    assert acct.page_ready(), "账号信息页标题或基本信息区未出现"
    attach_screenshot(acct.driver, "账号信息页")


@allure.title("账号信息页邮箱格式合法")
def test_account_email_format(home):
    acct = open_account_info(home)
    email = acct.email_text()
    logger.info("当前账号邮箱: %s", email)
    allure.attach(email or "(空)", name="邮箱", attachment_type=allure.attachment_type.TEXT)
    attach_screenshot(acct.driver, "邮箱显示")
    assert email, "未找到邮箱值"
    assert _EMAIL_RE.fullmatch(email), f"邮箱格式异常: {email!r}"


@allure.title("退出登录/注销账号按钮存在（只看不点）")
def test_account_danger_buttons_exist(home):
    acct = open_account_info(home)
    assert acct.logout_button_visible(), "「退出登录」按钮未显示"
    assert acct.delete_button_visible(), "「注销账号」按钮未显示"
    attach_screenshot(acct.driver, "危险按钮存在性")
    acct.back()  # 看完就走，绝不点
