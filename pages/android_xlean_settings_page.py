"""xLean 设备设置页 + 账号信息页 Page Object（教学示范：注释即文档）。

导航路径：
  设备设置: 首页右上角「设备设置」文字 -> 设备设置页（三组共 13 个入口）
  账号信息: 抽屉菜单「账号信息」 -> 账号信息页（基本信息/账号管理/退出登录）

安全约定：账号信息页的 退出登录/注销账号/切换/设置密码 一律只断言存在,
  绝不点击（会动真实账号状态）。
"""
from __future__ import annotations

import re
import time

from appium.webdriver.common.appiumby import AppiumBy

from common.base_page import BasePage
from common.logger import logger

_PKG = "ai.xlean.android.debug"

# 文字定位模板（该 App 无 resource-id）
_X_TEXT = '//*[@text="{}"]'


class DeviceSettingsPage(BasePage):
    """设备设置页：三组入口的只读检查。"""

    # ---------------- 定位符 ----------------
    _page_title = (AppiumBy.XPATH, _X_TEXT.format("设备设置"))
    # 分组标题
    _group_clean = (AppiumBy.XPATH, _X_TEXT.format("清洁设置"))
    _group_control = (AppiumBy.XPATH, _X_TEXT.format("设备控制"))
    _group_manage = (AppiumBy.XPATH, _X_TEXT.format("设备管理"))
    # 组内入口（断言存在即可，不点）
    _entries = [
        ("清洁记录", "清洁记录"), ("清洁任务", "清洁任务"),
        ("地图管理", "地图管理"), ("耗材管理", "耗材管理"),
        ("手杆控制", "手杆控制"), ("基站设置", "基站设置"),
        ("视频管家", "视频管家"), ("设备信息", "设备信息"),
        ("固件升级", "固件升级"), ("设备共享", "设备共享"),
    ]

    # ---------------- 断言素材 ----------------
    def page_title_visible(self) -> bool:
        return self.is_visible(self._page_title, timeout=8)

    def group_headers_visible(self) -> bool:
        return all(self.is_visible(g, timeout=3)
                   for g in (self._group_clean, self._group_control, self._group_manage))

    def missing_entries(self) -> list[str]:
        """返回没显示出来的入口名（空列表 = 全在）。

        页面有 13 个入口, 一屏放不下 —— 底部的「设备共享」等要上滑才可见。
        策略: 先查一遍, 有缺的就上滑一屏再查缺的, 最多滑 3 次。
        """
        missing = [name for name, text in self._entries
                   if not self.is_visible((AppiumBy.XPATH, _X_TEXT.format(text)), timeout=1.5)]
        for _ in range(3):
            if not missing:
                break
            self.swipe("up", times=1)
            missing = [name for name, text in self._entries
                       if name in missing
                       and not self.is_visible((AppiumBy.XPATH, _X_TEXT.format(text)), timeout=1.5)]
        return missing


class AccountInfoPage(BasePage):
    """账号信息页：已登录态的只读检查。"""

    # ---------------- 定位符 ----------------
    _page_title = (AppiumBy.XPATH, _X_TEXT.format("账号信息"))
    _section_basic = (AppiumBy.XPATH, _X_TEXT.format("基本信息"))
    _section_manage = (AppiumBy.XPATH, _X_TEXT.format("账号管理"))
    _label_account = (AppiumBy.XPATH, _X_TEXT.format("账号"))
    _label_email = (AppiumBy.XPATH, _X_TEXT.format("邮箱"))
    # 邮箱值: 任何包含 @ 的文本节点
    _email_value = (AppiumBy.XPATH, '//*[contains(@text,"@")]')
    # 危险操作按钮（只断言存在, 绝不点击）
    _logout_btn = (AppiumBy.XPATH, _X_TEXT.format("退出登录"))
    _delete_btn = (AppiumBy.XPATH, _X_TEXT.format("注销账号"))

    # ---------------- 断言素材 ----------------
    def page_ready(self) -> bool:
        return self.is_visible(self._page_title, timeout=8) and \
            self.is_visible(self._section_basic, timeout=3)

    def email_text(self) -> str:
        """取第一个长得像邮箱的文本（跳过「邮箱」标签本身）。

        最大的坑(实测): 账号页是异步渲染的, 邮箱值加载进来时页面会重渲染,
        刚 find 到的元素引用立刻失效 -> StaleElementReferenceException。
        所以访问 el.text 必须容 stale 异常, 失效就下一轮重找; 总窗 60s。
        另: 「忽略推荐？」等弹窗会晚到挡页面(原生对话框把底层 Activity
        挤出无障碍树) —— 每轮先关弹窗。
        实测: 无线 adb 连跑 12+ 条用例后设备变慢, 邮箱加载可能超过 60s
        (证据截图里值已显示但轮询已超时) —— 总窗放宽到 120s。
        """
        from pages.android_xlean_page import dismiss_popups
        from selenium.common.exceptions import StaleElementReferenceException
        deadline = time.time() + 120
        while time.time() < deadline:
            try:
                for el in self.find_all(self._email_value):
                    t = (el.text or "").strip()
                    if "@" in t and t != "邮箱":
                        return t
            except StaleElementReferenceException:
                pass  # 页面重渲染, 元素引用失效, 下一轮重找
            dismiss_popups(self)
            time.sleep(1)
        return ""

    def logout_button_visible(self) -> bool:
        return self.is_visible(self._logout_btn, timeout=3)

    def delete_button_visible(self) -> bool:
        return self.is_visible(self._delete_btn, timeout=2)


def open_device_settings(home: BasePage) -> DeviceSettingsPage:
    """首页 -> 设备设置页（公共导航动作，供测试复用）。

    注意: 首页右上角的「设备设置」是图标按钮, 文字挂在 content-desc 上
    (实测 dump: text='' desc='设备设置'), 必须用 accessibility id 定位;
    设备设置页内部的标题「设备设置」才是 text。
    """
    home.click((AppiumBy.ACCESSIBILITY_ID, "设备设置"), desc="首页右上角-设备设置")
    return DeviceSettingsPage(home.driver)


def open_account_info(home: BasePage) -> AccountInfoPage:
    """首页 -> 抽屉菜单 -> 账号信息页。"""
    home.click((AppiumBy.ACCESSIBILITY_ID, "打开菜单"), desc="打开菜单")
    home.click((AppiumBy.XPATH, _X_TEXT.format("账号信息")), desc="菜单-账号信息")
    return AccountInfoPage(home.driver)
