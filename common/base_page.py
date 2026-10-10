"""BasePage: 所有 Page Object 的基类。

封装设计:
1. 定位符(元素)采用"双端字典"形式, 自动按当前平台取用:
       LOGIN_BTN = {
           "android": (AppiumBy.ID, "com.demo:id/login"),
           "ios":     (AppiumBy.ACCESSIBILITY_ID, "登录"),
           # 可选 "default" 兜底
       }
   也支持字符串简写: "id=xxx" | "xpath=//xxx" | "aid=xxx" | "name=xxx" | "class=xxx"
2. 所有动作自动打日志 + 失败时自动截图并抛出清晰异常, 方便 Allure 回溯。
"""
from __future__ import annotations

import time

from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.config import config
from common.logger import logger
from common.utils.allure_utils import attach_screenshot
from common.utils.ui_dump import dump_page

_SHORT_PREFIX = (
    ("id=", AppiumBy.ID),
    ("xpath=", AppiumBy.XPATH),
    ("aid=", AppiumBy.ACCESSIBILITY_ID),
    ("name=", AppiumBy.NAME),
    ("class=", AppiumBy.CLASS_NAME),
)


class BasePage:
    def __init__(self, driver, timeout: int | None = None):
        self.driver = driver
        self.platform = getattr(config, "platform", "android") or "android"
        self.timeout = timeout or config.explicit_wait

    # ---------------- 定位符解析 ----------------
    def _resolve(self, locator):
        """把 双端字典/字符串简写/tuple 归一化为 (AppiumBy, value)。"""
        if isinstance(locator, dict):
            key = self.platform if self.platform in locator else "default"
            if key not in locator:
                raise ValueError(
                    f"定位符缺少平台 {self.platform} 或 default: {list(locator.keys())}")
            locator = locator[key]
        if isinstance(locator, str):
            for prefix, by in _SHORT_PREFIX:
                if locator.startswith(prefix):
                    return (by, locator[len(prefix):])
            raise ValueError(f"不支持的定位符简写: {locator} (需以 id=/xpath=/aid=/name=/class= 开头)")
        if isinstance(locator, (tuple, list)) and len(locator) == 2:
            return (locator[0], locator[1])
        raise ValueError(f"无法识别的定位符: {locator!r}")

    # ---------------- 查找 ----------------
    def find(self, locator, timeout: int | None = None, desc: str = ""):
        by, value = self._resolve(locator)
        wait = WebDriverWait(self.driver, timeout or self.timeout,
                             poll_frequency=config.poll_frequency)
        try:
            return wait.until(EC.presence_of_element_located((by, value)))
        except Exception:
            attach_screenshot(self.driver, f"find_fail_{desc or value}")
            raise TimeoutError(f"[{desc or '查找元素'}] 等待 {timeout or self.timeout}s 未出现: {by}={value}")

    def find_all(self, locator, timeout: int | None = None):
        by, value = self._resolve(locator)
        wait = WebDriverWait(self.driver, timeout or self.timeout,
                             poll_frequency=config.poll_frequency)
        try:
            return wait.until(lambda d: d.find_elements(by, value))
        except Exception:
            return []

    def is_visible(self, locator, timeout: float = 0.5) -> bool:
        """快速可见性判断(不抛错)。"""
        try:
            by, value = self._resolve(locator)
            if timeout > 0:
                WebDriverWait(self.driver, timeout).until(
                    EC.visibility_of_element_located((by, value)))
            else:
                self.driver.find_element(by, value)
            return True
        except Exception:  # noqa: BLE001
            return False

    # ---------------- 动作 ----------------
    def click(self, locator, desc: str = "", timeout: int | None = None):
        el = self.find(locator, timeout=timeout, desc=desc or "click")
        tag = desc or f"{self._resolve(locator)}"
        try:
            el.click()
            logger.info("[点击] %s", tag)
        except Exception as exc:
            attach_screenshot(self.driver, "click_fail")
            raise RuntimeError(f"点击失败({tag}): {exc}") from exc

    def send_keys(self, locator, text: str, desc: str = "", clear: bool = True,
                  timeout: int | None = None):
        el = self.find(locator, timeout=timeout, desc=desc or "input")
        tag = desc or f"{self._resolve(locator)}"
        if clear:
            try:
                el.clear()
            except Exception:  # noqa: BLE001
                pass
        el.send_keys(text)
        logger.info("[输入] %s <= %s", tag, text)

    def get_text(self, locator, timeout: int | None = None) -> str:
        el = self.find(locator, timeout=timeout, desc="get_text")
        try:
            text = el.text or ""
        except Exception:  # noqa: BLE001
            text = el.get_attribute("text") or el.get_attribute("label") or ""
        return (text or "").strip()

    def wait_visible(self, locator, timeout: int | None = None) -> WebElement:
        by, value = self._resolve(locator)
        WebDriverWait(self.driver, timeout or self.timeout,
                      poll_frequency=config.poll_frequency).until(
            EC.visibility_of_element_located((by, value)))
        return self.driver.find_element(by, value)

    def wait_gone(self, locator, timeout: int | None = None) -> bool:
        by, value = self._resolve(locator)
        try:
            WebDriverWait(self.driver, timeout or self.timeout,
                          poll_frequency=config.poll_frequency).until_not(
                EC.presence_of_element_located((by, value)))
            return True
        except Exception:  # noqa: BLE001
            return False

    def wait_text(self, text: str, timeout: int | None = None) -> bool:
        """等待页面上出现包含指定文本的任意节点。"""
        try:
            WebDriverWait(self.driver, timeout or self.timeout,
                          poll_frequency=config.poll_frequency).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, f"//*[contains(@text,'{text}') or contains(@label,'{text}') "
                                     f"or contains(@content-desc,'{text}') or contains(@name,'{text}')]")))
            return True
        except Exception:  # noqa: BLE001
            return False

    # ---------------- 滑动 ----------------
    def swipe(self, direction: str = "up", times: int = 1, duration_ms: int = 500):
        """direction: up/down/left/right。优先驱动自带 swipe, 缺失时用 W3C 触摸动作降级。"""
        size = self.driver.get_window_size()
        w, h = int(size["width"]), int(size["height"])
        d = {
            "up":    (w // 2, int(h * 0.75), w // 2, int(h * 0.25)),
            "down":  (w // 2, int(h * 0.25), w // 2, int(h * 0.75)),
            "left":  (int(w * 0.85), h // 2, int(w * 0.15), h // 2),
            "right": (int(w * 0.15), h // 2, int(w * 0.85), h // 2),
        }.get(direction)
        if not d:
            raise ValueError(f"direction 需为 up/down/left/right, 收到: {direction}")
        for _ in range(times):
            try:
                self.driver.swipe(*d, duration=duration_ms)   # type: ignore[attr-defined]
            except AttributeError:
                self._w3c_swipe(d, duration_ms)
            time.sleep(0.5)
        logger.info("[滑动] %s x%d", direction, times)

    def _w3c_swipe(self, d: tuple, duration_ms: int):
        from selenium.webdriver.common.action_chains import ActionChains
        chain = ActionChains(self.driver)
        chain.w3c_actions.pointer_action.move_to_location(d[0], d[1])
        chain.w3c_actions.pointer_action.pointer_down()
        chain.w3c_actions.pointer_action.move_to_location(d[2], d[3],
                                                          duration=duration_ms)
        chain.w3c_actions.pointer_action.release()
        chain.perform()

    # ---------------- 系统操作 ----------------
    def back(self):
        try:
            self.driver.back()
            logger.info("[系统] back")
        except Exception:  # noqa: BLE001
            logger.warning("[系统] back 不可用(忽略)")

    def hide_keyboard(self):
        try:
            self.driver.hide_keyboard()
        except Exception:  # noqa: BLE001
            pass

    # ---------------- 产物: 截图 / dump ----------------
    def screenshot(self, name: str = "page") -> str | None:
        path = attach_screenshot(self.driver, name)
        return str(path) if path else None

    def dump(self, name: str = "page") -> str:
        path = dump_page(self.driver, name)
        return str(path)
