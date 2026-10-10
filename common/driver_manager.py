"""Appium 会话管理(单例)。

- Android:  UiAutomator2 (支持真机 + 模拟器, 无 adb 时按配置 udid/deviceName)
- iOS:      XCUITest     (仅 macOS + Xcode; 模拟器留空 udid 自动选择)

App 选择优先级: --app 指定文件 > 自动扫描 apps/ 目录 > 启动设备上已安装的配置包。

capabilities 构造说明:
  Appium 2 要求"驱动专属能力"带 appium: 前缀(如 appium:automationName)。
  这里先组好完整 dict, 再由平台对应 Typed Options 装载——
  经实测 appium-python-client 6.x, Typed Options 会为已知键自动加前缀,
  对已带前缀的键原样透传; platformName 等 W3C 标准键保持不带前缀。
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from common.config import Config, config
from common.logger import logger

# Appium 2 中需要 appium: 前缀的驱动专属能力(按平台求并集)
_APPIUM_PREFIXED = {
    "automationName", "app", "appPackage", "appActivity", "appWaitForLaunch",
    "udid", "noReset", "fullReset", "autoGrantPermissions",
    "unicodeKeyboard", "resetKeyboard", "newCommandTimeout",
    "bundleId", "autoAcceptAlerts", "wdaLocalPort", "usePrebuiltWDA",
    "platformVersion", "appWaitDuration", "disableWindowAnimation",
}


class DriverManager:
    _driver: Any = None
    _driver_kwargs: dict = {}

    # ---------------- 对外 API ----------------
    @classmethod
    def create_driver(cls, platform: str | None = None, app_path: Path | str | None = None,
                      udid: str | None = None, server_url: str | None = None,
                      extra_caps: dict | None = None) -> Any:
        """创建并缓存 Appium 会话。appium-python-client 在方法内延迟导入。"""
        from appium import webdriver

        platform = (platform or config.platform or "android").lower()
        caps = cls.build_caps(platform, app_path=app_path, udid=udid, extra_caps=extra_caps)
        url = server_url or config.server_url

        logger.info("[Driver] 连接 Appium Server: %s (platform=%s)", url, platform)
        logger.info("[Driver] capabilities: %s", {k: v for k, v in caps.items()
                                                  if k != "app" and not str(v).endswith(".apk")})

        options = cls._make_options(platform, caps)
        driver = webdriver.Remote(url, options=options)
        try:
            driver.implicitly_wait(config.implicit_wait)
        except Exception as exc:  # noqa: BLE001
            # Appium 3.x + 新版 uiautomator2 驱动会把 /timeouts 代理到设备端，
            # 部分组合下设备端不认该路由(404)。隐式等待非必需，显式等待不受影响。
            logger.warning("[Driver] implicitly_wait 不被当前服务端组合支持(已忽略): %s", exc)

        cls._driver = driver
        cls._driver_kwargs = dict(platform=platform, app_path=app_path,
                                  udid=udid, server_url=url)
        logger.info("[Driver] 会话创建成功 sessionId=%s", getattr(driver, "session_id", None))
        return driver

    @classmethod
    def get_driver(cls) -> Any:
        if cls._driver is None:
            cls.create_driver(**cls._driver_kwargs)
        return cls._driver

    @classmethod
    def quit(cls) -> None:
        if cls._driver is not None:
            try:
                cls._driver.quit()
                logger.info("[Driver] 会话已正常退出")
            except Exception as exc:  # noqa: BLE001
                logger.warning("[Driver] 会话退出异常(忽略): %s", exc)
            finally:
                cls._driver = None

    # ---------------- capabilities ----------------
    @staticmethod
    def build_caps(platform: str, app_path: Path | str | None = None,
                   udid: str | None = None, extra_caps: dict | None = None) -> dict:
        base: dict = config.platform_cfg(platform)
        caps: dict[str, Any] = {
            "platformName": "Android" if platform == "android" else "iOS",
            "automationName": base.get("automation_name")
                              or ("UiAutomator2" if platform == "android" else "XCUITest"),
            "newCommandTimeout": int(config.get("appium.command_timeout_ms", 300000) // 1000),
            "noReset": bool(base.get("no_reset", True)),
        }

        # ---------- 设备 ----------
        if platform == "android":
            found_udid = udid or config.udid or base.get("udid") \
                         or DriverManager._detect_android_udid()
            if found_udid:
                caps["udid"] = str(found_udid)
            caps.setdefault("deviceName", str(base.get("device_name") or "Android"))
            if base.get("auto_grant_permissions") is not None:
                caps["autoGrantPermissions"] = bool(base["auto_grant_permissions"])
            for key, cap in (("unicode_keyboard", "unicodeKeyboard"),
                             ("reset_keyboard", "resetKeyboard")):
                if base.get(key) is not None:
                    caps[cap] = bool(base[key])
        else:  # ios
            found_udid = udid or config.udid or base.get("udid")
            if found_udid and str(found_udid).upper() != "AUTO":
                caps["udid"] = str(found_udid)
            caps.setdefault("deviceName", str(base.get("device_name") or "iPhone"))
            if base.get("wda_local_port"):
                caps["wdaLocalPort"] = int(base["wda_local_port"])
            if base.get("use_prebuilt_wda") is not None:
                caps["usePrebuiltWDA"] = bool(base["use_prebuilt_wda"])
            if base.get("auto_accept_alerts") is not None:
                caps["autoAcceptAlerts"] = bool(base["auto_accept_alerts"])

        pv = base.get("platform_version")
        if pv:
            caps["platformVersion"] = str(pv)

        # ---------- App ----------
        app: Path | None = None
        if app_path:
            p = Path(app_path).resolve()
            app = p if p.exists() else None
            if app_path and not app:
                logger.warning("[Driver] 找不到 --app 文件: %s, 改为启动已配置的已安装应用",
                               app_path)
        else:
            app = config.resolve_app_path()

        if platform == "android":
            if app:
                caps["app"] = str(app)
            else:
                if base.get("app_package"):
                    caps["appPackage"] = base["app_package"]
                if base.get("app_activity"):
                    caps["appActivity"] = base["app_activity"]
        else:
            if app:
                caps["app"] = str(app)
            elif base.get("bundle_id"):
                caps["bundleId"] = base["bundle_id"]

        # ---------- 追加自定义 capability(自动补 appium: 前缀) ----------
        ex = dict(base.get("extra_capabilities") or {})
        if extra_caps:
            ex.update(extra_caps)
        for key, value in ex.items():
            caps[DriverManager._maybe_prefix(key)] = value
        return {k: v for k, v in caps.items() if v is not None}

    # ---------------- Options 装载 ----------------
    @staticmethod
    def _maybe_prefix(key: str) -> str:
        """已知的驱动专属能力自动补 appium: 前缀; 已带前缀或 W3C 键保持原样。"""
        if key.startswith("appium:") or key.startswith("goog:") \
                or key.startswith("webkit:"):
            return key
        if key in _APPIUM_PREFIXED:
            return f"appium:{key}"
        return key

    @staticmethod
    def _make_options(platform: str, caps: dict) -> Any:
        """按平台选择 Typed Options 并装载(为已知键补 appium: 前缀)。"""
        if platform == "android":
            from appium.options.android import UiAutomator2Options as OptCls
        else:
            from appium.options.ios import XCUITestOptions as OptCls

        prepared = {DriverManager._maybe_prefix(k): v for k, v in caps.items()}
        options = OptCls().load_capabilities(prepared)
        # 构造完成校验: 必须带上 automationName, 否则驱动无法路由
        final_caps = options.to_capabilities()
        if not any(k.endswith("automationName") for k in final_caps):
            raise RuntimeError("capabilities 缺少 automationName, 无法确定 Appium 驱动")
        return options

    # ---------------- 工具 ----------------
    @staticmethod
    def _detect_android_udid() -> str | None:
        """自动探测 adb devices 中第一个在线设备。"""
        if not shutil.which("adb"):
            return None
        try:
            out = subprocess.run(["adb", "devices"], capture_output=True,
                                 text=True, timeout=10).stdout
            for line in out.splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    return parts[0]
        except Exception:  # noqa: BLE001
            pass
        return None
