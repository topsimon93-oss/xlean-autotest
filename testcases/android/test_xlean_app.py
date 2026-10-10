"""xLean App 核心链路测试(只读, 不干扰真实机器人)。

覆盖: 首页渲染 / 设备电量 / 清洁状态 / 底部导航(计划·探索) / 抽屉菜单开合。
安全约定: 不点 进入设备/基站/临时清洁暂停停止, 不点菜单内任何功能项。
运行:
    python -m pytest testcases/android/test_xlean_app.py --platform android -v
"""
from __future__ import annotations

import re

import allure
import pytest

from common.logger import logger
from common.utils.allure_utils import attach_screenshot
from pages.android_xlean_page import XLeanHomePage

pytestmark = [pytest.mark.android]


@pytest.fixture
def home(driver) -> XLeanHomePage:
    """起点=「真·首页」(弹窗关掉、「进入设备」可见)。

    会话前已由 conftest 在 adb 层冷启动 App(会话内杀 App 会弄脏 uiautomator2
    连接, 之后 find 静默失败 —— 实测大坑), 这里只等首页就绪 + 关弹窗。
    """
    page = XLeanHomePage(driver)
    page.dismiss_popups()
    if not page.home_ready():
        page.wait_visible(page._enter_device, timeout=20)
        page.dismiss_popups()
    return page


@allure.title("首页正常渲染: 设备名/进入设备/基站")
def test_home_screen_renders(home: XLeanHomePage):
    # 只断言稳定元素; 「临时清洁」等清洁卡是动态的, 由 test_clean_status_card 候选列表覆盖
    # App V0.22.6.0 起首页已移除「xLean TR1」设备名文本, 改为「进入设备」入口(见 home_ready 注释)
    assert home.home_ready(), "首页未就绪（「进入设备」入口缺失）"
    assert home.is_visible(home._enter_device, timeout=5), "「进入设备」入口缺失"
    assert home.is_visible(home._base_station, timeout=5), "「基站」入口缺失"
    attach_screenshot(home.driver, "首页渲染")


@allure.title("设备电量显示为合法百分比")
def test_battery_percent_format(home: XLeanHomePage):
    text = home.battery_text()
    logger.info("当前电量文本: %s", text)
    attach_screenshot(home.driver, "电量显示")
    assert text, "未找到电量百分比元素"
    assert re.fullmatch(r"\d{1,3}%", text), f"电量格式异常: {text!r}"
    assert 0 <= int(text.rstrip("%")) <= 100, f"电量数值越界: {text}"


@allure.title("清洁入口卡片存在(动态候选列表)")
def test_clean_status_card(home: XLeanHomePage):
    status = home.clean_status_text()
    logger.info("当前清洁状态: %s", status or "(未识别到已知状态)")
    attach_screenshot(home.driver, "清洁状态")
    # 首页清洁卡是动态的: 清洁中=「临时清洁」, 清洁结束=AI推荐/全屋清扫等推荐卡
    # 断言"至少有一张清洁入口卡片", 不写死某一个(否则清洁一结束用例就假失败)
    assert home.any_clean_card_visible(), \
        "首页没有任何清洁入口卡片(候选: 临时清洁/全屋清扫/全屋快速清洁/全屋静音清洁)"
    allure.attach(status or "未知", name="当前状态",
                  attachment_type=allure.attachment_type.TEXT)


@allure.title("底部导航-计划: 占位页显示「敬请期待」")
def test_plan_tab_placeholder(home: XLeanHomePage):
    home.go_plan_tab()
    assert home.placeholder_visible(), "计划页未显示「敬请期待」"
    attach_screenshot(home.driver, "计划页")
    home.go_home_tab()
    # 切回首页渲染需要几秒, 偶发弹窗也会挡 —— 先关弹窗再等(实测 5s 偶尔不够)
    home.dismiss_popups()
    assert home.is_visible(home._device_name, timeout=10) or home.home_ready(), \
        "返回首页后首页元素丢失"
    attach_screenshot(home.driver, "计划页返回首页")


@allure.title("底部导航-探索: 页面可切换且可返回首页")
def test_explore_tab_placeholder(home: XLeanHomePage):
    """探索页为 Compose 界面且内容区未暴露无障碍文本(2026-10-10 实测, 仅底部Tab可见),
    文本断言不可行 —— 改为行为级验证: 能切到探索页、能切回、首页恢复正常。"""
    home.go_explore_tab()
    attach_screenshot(home.driver, "探索页(内容区无障碍文本缺失, 需人工看截图)")
    home.go_home_tab()
    home.dismiss_popups()
    assert home.is_visible(home._device_name, timeout=15) or home.home_ready(), \
        "探索页切回首页后首页元素丢失"
    attach_screenshot(home.driver, "探索页返回首页")


@allure.title("抽屉菜单: 打开可见菜单项, 返回键收起")
def test_menu_open_close(home: XLeanHomePage):
    home.open_menu()
    assert home.menu_items_visible(), "菜单打开后未见「我的/关于」菜单项"
    attach_screenshot(home.driver, "菜单展开")
    home.close_menu()
    assert home.menu_closed(), "返回键未收起菜单"
