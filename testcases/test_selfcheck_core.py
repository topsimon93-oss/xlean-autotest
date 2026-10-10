"""框架自检(纯逻辑, 不依赖设备/Appium Server, 任何平台都会跑)。

覆盖: ① 双端定位符解析  ② 配置双层深合并与 CLI 覆盖。
跑批时如这三条挂了, 说明是框架代码/配置问题, 先修框架再看业务。
"""
from __future__ import annotations

import allure
import pytest
import yaml

from common.base_page import BasePage
from common.config import Config

pytestmark = [pytest.mark.generic, pytest.mark.selfcheck]


@allure.title("[自检] 双端定位符字典按平台取用 + 字符串简写解析")
def test_locator_resolution(monkeypatch):
    monkeypatch.setattr(Config.instance(), "platform", "android")
    page = BasePage(driver=None, timeout=1)

    # 双端字典按 android 取用
    loc = {"android": ("id", "com.demo:id/btn"),
           "ios": ("name", "登录"),
           }
    assert page._resolve(loc) == ("id", "com.demo:id/btn")

    # 切到 ios 后取 ios 分支
    monkeypatch.setattr(Config.instance(), "platform", "ios")
    page2 = BasePage(driver=None, timeout=1)
    assert page2._resolve(loc) == ("name", "登录")

    # 缺平台分支时报清晰错误
    with pytest.raises(ValueError):
        page2._resolve({"android": ("id", "x")})

    # 字符串简写
    from appium.webdriver.common.appiumby import AppiumBy
    assert page2._resolve("aid=登录") == (AppiumBy.ACCESSIBILITY_ID, "登录")
    assert page2._resolve("xpath=//*[@text='a']") == (AppiumBy.XPATH, "//*[@text='a']")
    assert page2._resolve("id=com.demo:id/a") == (AppiumBy.ID, "com.demo:id/a")
    with pytest.raises(ValueError):
        page2._resolve("text=不支持")


@allure.title("[自检] global 与 local.yaml 深合并, local 优先生效")
def test_config_deep_merge(tmp_path, monkeypatch):
    (tmp_path / "global.yaml").write_text(
        "wait:\n  implicit: 10\n  explicit: 20\n"
        "android:\n  app_package: com.a.global\n"
        "extra_global: 1\n", encoding="utf-8")
    (tmp_path / "local.yaml").write_text(
        "wait:\n  implicit: 3\n"
        "android:\n  app_package: com.a.local\n", encoding="utf-8")

    cfg = Config(config_dir=tmp_path)
    cfg.reload()
    assert cfg.get("wait.implicit") == 3           # local 覆盖
    assert cfg.get("wait.explicit") == 20          # global 保留
    assert cfg.get("android.app_package") == "com.a.local"
    assert cfg.get("extra_global") == 1


@allure.title("[自检] CLI 覆盖参数生效")
def test_config_cli_override(monkeypatch):
    cfg = Config.instance()
    cfg.set_cli(platform="ios", udid="ABCD-1234",
                server="http://192.168.1.2:4723")
    assert cfg.platform == "ios"
    assert cfg.udid == "ABCD-1234"
    assert cfg.server_url == "http://192.168.1.2:4723"
    # 还原, 避免影响其它用例
    cfg.set_cli(platform="android", udid=None, server=None)
