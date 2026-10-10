"""通用冒烟测试 —— 对"任意 App"可用, 不需要任何元素/业务知识。

覆盖: ① 安装并启动  ② 首屏可渲染  ③ 短时稳定性(无崩溃)  ④ UI dump(xml)
      ⑤ 首屏截图。产物(截图+xml)会自动挂到 Allure 并落盘 screenshots/ 与 reports/dumps/,
      是后续"AI 分析页面结构 -> 生成 Page Object 与业务用例"的输入素材。

用法(Android 示例):
    python -m pytest --platform android --app apps/你的应用.apk
"""
from __future__ import annotations

import time

import allure
import pytest

from common.config import config
from common.logger import logger
from common.utils.allure_utils import attach_screenshot
from common.utils.ui_dump import dump_page

pytestmark = [pytest.mark.generic, pytest.mark.smoke]


@allure.title("① App 安装并成功启动")
def test_01_install_and_launch(driver, settle_seconds):
    time.sleep(settle_seconds)  # 等待首屏稳定
    info: dict = {}
    if config.platform == "android":
        pkg = driver.current_package
        info["package"] = pkg
        try:
            info["activity"] = driver.current_activity
        except Exception:  # noqa: BLE001
            pass
        logger.info("当前前台包名: %s", pkg)
        assert pkg, "读取不到当前前台 App 包名, 疑似未启动或已崩溃"
    else:
        src = driver.page_source
        assert src, "page_source 为空, 疑似启动失败"
    attach_screenshot(driver, "01_启动后首屏")
    allure.attach(str(info), name="app_info", attachment_type=allure.attachment_type.TEXT)


@allure.title("② 首屏 UI 可渲染(非空)")
def test_02_first_screen_render(driver):
    source = driver.page_source
    assert source and len(source) > 0, "page_source 为空"
    nodes = driver.find_elements("xpath", "//*")
    logger.info("首屏元素节点数量: %d", len(nodes))
    assert nodes, "首屏没有任何可识别节点"
    allure.attach(source, name="page_source", attachment_type=allure.attachment_type.XML)


@allure.title("③ 短时稳定性检查(静置无崩溃)")
def test_03_short_stability(driver, settle_seconds):
    time.sleep(settle_seconds)
    if config.platform == "android":
        activity = driver.current_activity
        logger.info("当前前台 Activity: %s", activity)
        assert activity, "静置后应用已退出或崩溃"
    assert len(driver.page_source) > 0, "静置后页面为空"
    attach_screenshot(driver, "03_静置后状态")


@allure.title("④ 保存 UI 层级 dump(供 AI/人工分析)")
def test_04_dump_ui_tree(driver, platform):
    path = dump_page(driver, "first_screen")
    assert path.exists(), "UI dump 文件未生成"
    logger.info("UI dump 已保存: %s", path)


@allure.title("⑤ 首屏截图存档")
def test_05_first_screen_screenshot(driver):
    path = attach_screenshot(driver, "first_screen")
    assert path and path.exists(), "截图未生成"
    logger.info("截图已保存: %s", path)
