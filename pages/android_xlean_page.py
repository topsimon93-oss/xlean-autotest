"""xLean App 首页 Page Object。

被测 App: ai.xlean.android.debug(扫地机器人控制端)。
界面特点: 元素基本没有 resource-id, 统一用 text 文字 / content-desc(无障碍标识)定位。
电量百分比用 UiAutomator 的 textMatches 正则定位(动态内容)。

安全约定(重要): 本 Page 只封装"只读/导航"动作,
  不提供 进入设备/基站/临时清洁暂停停止 等会干扰真实机器人的操作。
"""
from __future__ import annotations

import re
import time

from appium.webdriver.common.appiumby import AppiumBy

from common.base_page import BasePage

# 文字定位(该 App 无 resource-id, 全靠 text)
_X_TEXT = '//*[@text="{}"]'

# ---------------- 弹窗处理(模块级, 首页/账号页等共用) ----------------
# 实测弹窗类型: 「重点区域AI推荐」(关闭)、「忽略推荐？」(忽略/去看看)等。
# 只点关闭类安全按钮: 「忽略」仅关掉推荐弹窗不跳转; 「去看看」会导航, 绝不点。
_SAFE_DISMISS_TEXTS = ("关闭", "我知道了", "知道了", "稍后再说", "取消", "忽略")
# 双匹配: 「关闭」在 content-desc 上(text 为空), 「取消/忽略」类通常是 text
_X_ANY = '//*[@text="{t}" or @content-desc="{t}"]'


def dismiss_popups(page) -> bool:
    """关掉挡路的弹窗(供所有 Page 复用)。返回是否有弹窗被关闭。"""
    closed = False
    for txt in _SAFE_DISMISS_TEXTS:
        loc = (AppiumBy.XPATH, _X_ANY.format(t=txt))
        if page.is_visible(loc, timeout=0.8):
            try:
                page.click(loc, desc=f"关闭弹窗[{txt}]")
                closed = True
                time.sleep(1)
            except Exception:  # noqa: BLE001
                pass
    return closed


class XLeanHomePage(BasePage):
    # ---------------- 定位符 ----------------
    # 首页核心元素
    # 设备名用前缀匹配: 设备名实际文本是 "xLean TR1 14"(带固件/版本后缀),
    # 精确匹配 @text="xLean TR1" 会失配(2026-10-09 实测坑)
    _device_name = (AppiumBy.XPATH, '//*[starts-with(@text, "xLean TR1")]')
    _enter_device = (AppiumBy.XPATH, _X_TEXT.format("进入设备"))
    _temp_clean = (AppiumBy.XPATH, _X_TEXT.format("临时清洁"))
    _base_station = (AppiumBy.XPATH, _X_TEXT.format("基站"))

    # 电量: 动态文本(62%->61%...), 优先取「设备电量」标识旁的百分比,
    # 兜底用 UiAutomator 正则(注意 Python 源码里写 "\\d" 才是正则的 \d)
    _battery_via_desc = (AppiumBy.XPATH,
                         '//*[@content-desc="设备电量"]/following-sibling::*[@text]')
    _battery_any = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textMatches("\\d+%")')

    # 底部导航
    _tab_home = (AppiumBy.XPATH, _X_TEXT.format("首页"))
    _tab_plan = (AppiumBy.XPATH, _X_TEXT.format("计划"))
    _tab_explore = (AppiumBy.XPATH, _X_TEXT.format("探索"))
    _placeholder = (AppiumBy.XPATH, _X_TEXT.format("敬请期待"))

    # 抽屉菜单: content-desc -> accessibility id
    _open_menu = (AppiumBy.ACCESSIBILITY_ID, "打开菜单")
    _menu_profile = (AppiumBy.XPATH, _X_TEXT.format("我的"))
    _menu_about = (AppiumBy.XPATH, _X_TEXT.format("关于"))

    # ---------------- 只读断言素材 ----------------
    def device_name_visible(self) -> bool:
        return self.is_visible(self._device_name, timeout=5)

    def home_ready(self) -> bool:
        """真·首页就绪判断。

        注意: 抽屉菜单里也有「xLean TR1」, 设备名可见不代表菜单已收起;
        「进入设备」只有首页才有, 菜单遮挡时不存在 —— 用它判断最稳。
        """
        return self.is_visible(self._enter_device, timeout=2)

    # ---------------- 弹窗处理 ----------------
    def dismiss_popups(self) -> bool:
        """关掉挡路的弹窗。委托模块级同名函数(账号页等也复用)。"""
        return dismiss_popups(self)

    def battery_text(self) -> str:
        """电量文本。首页动态区重渲染会让元素引用失效(stale), 容错重找一轮。"""
        from selenium.common.exceptions import StaleElementReferenceException
        for _ in range(3):
            try:
                els = self.find_all(self._battery_via_desc)
                if els and els[0].text.strip():
                    return els[0].text.strip()
                els = self.find_all(self._battery_any)  # 兜底: 页面上任意百分比
                if els:
                    return els[0].text
                return ""
            except StaleElementReferenceException:
                time.sleep(1)  # 页面重渲染, 重找
        return ""

    def clean_status_text(self) -> str:
        """清洁状态(清洁中/充电中/清洁完成等), 动态内容只取回报告不做硬断言。"""
        for kw in ("清洁中", "充电中", "清洁完成", "回充中", "待机"):
            el = self.find_all((AppiumBy.XPATH, _X_TEXT.format(kw)))
            if el:
                return kw
        return ""

    # 清洁入口卡片: 首页这块是动态的 —— 清洁中显示「临时清洁」,
    # 清洁结束后换成 AI 推荐/全屋清扫/全屋快速清洁/全屋静音清洁 等推荐卡
    _clean_card_texts = ("临时清洁", "全屋清扫", "全屋快速清洁", "全屋静音清洁")

    def any_clean_card_visible(self) -> bool:
        """首页清洁入口卡片存在性(动态候选列表, 不写死某一个)。"""
        for txt in self._clean_card_texts:
            if self.is_visible((AppiumBy.XPATH, _X_TEXT.format(txt)), timeout=1):
                return True
        return False

    # ---------------- 导航动作 ----------------
    def go_plan_tab(self) -> "XLeanHomePage":
        self.click(self._tab_plan, desc="底部导航-计划")
        return self

    def go_explore_tab(self) -> "XLeanHomePage":
        self.click(self._tab_explore, desc="底部导航-探索")
        return self

    def go_home_tab(self) -> "XLeanHomePage":
        self.click(self._tab_home, desc="底部导航-首页")
        return self

    def placeholder_visible(self) -> bool:
        return self.is_visible(self._placeholder, timeout=5)

    def explore_content_visible(self) -> bool:
        """探索页真实内容（App 更新后不再是占位页）：标题 Explore 或 Video Guides 任一可见即算就绪。"""
        for t in ("Explore", "Video Guides", "Documentation Center"):
            if self.is_visible(
                (AppiumBy.XPATH, '//*[@text="{t}" or @content-desc="{t}"]'.format(t=t)),
                timeout=6,
            ):
                return True
        return False

    # ---------------- 抽屉菜单 ----------------
    def open_menu(self) -> "XLeanHomePage":
        self.click(self._open_menu, desc="打开菜单")
        return self

    def menu_items_visible(self) -> bool:
        return self.is_visible(self._menu_profile, timeout=5) and \
            self.is_visible(self._menu_about, timeout=2)

    def close_menu(self) -> "XLeanHomePage":
        self.back()  # 返回键收起, 不点菜单内任何功能
        return self

    def menu_closed(self) -> bool:
        return not self.is_visible(self._menu_profile, timeout=2)
