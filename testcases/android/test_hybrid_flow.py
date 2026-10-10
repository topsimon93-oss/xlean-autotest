# -*- coding: utf-8 -*-
"""
混合分工示例：Appium 管固定断言，Artemis 管探索路径。

分工原则（省 token 的关键）：
  - 回归断言（元素存在、文本校验、固定流程）→ Appium Page Object，零 token，快且稳
  - 探索性路径（"找到那个设置项"、"确认页面能打开"）→ Artemis 用自然语言跑

运行前：
  1. Artemis daemon 已起：cd D:/projects/artemis && uv run artemis ui
  2. 真机已连：adb devices 能看到 device
  3. 装了 artemis-client（见 common/artemis_client_wrapper.py 顶部注释）

运行：
  python -m pytest testcases/android/test_hybrid_flow.py -s --platform android
  （需要 pytest-asyncio；如未装：pip install pytest-asyncio）

注意：Artemis 部分会消耗 OpenRouter token，仅在需要探索时跑；
     纯回归请走 Appium，别让 Artemis 干 Appium 能干的事。
"""
from __future__ import annotations

import allure
import pytest

from common.artemis_client_wrapper import ArtemisWrapper

pytestmark = pytest.mark.android


# ---------------------------------------------------------------------------
# Artemis 探索任务 fixture（按需启用）
# ---------------------------------------------------------------------------
@pytest.fixture
def artemis():
    """Artemis 封装。设备序列号用环境变量 ARTEMIS_DEVICE 或 AppAutoTest 配置。"""
    return ArtemisWrapper()


# ---------------------------------------------------------------------------
# 例 1：纯 Appium 回归（零 token，快）
# ---------------------------------------------------------------------------
@allure.title("Appium 回归：启动 App 后首屏稳定")
def test_app_launch_settles(driver, settle_seconds):
    """固定流程 + 简单断言，交给 Appium，不调模型。"""
    assert driver is not None
    # 首屏稳定后做一次基础断言（例：当前 activity 非空）
    activity = driver.current_activity
    assert activity, "启动后应能读到当前 activity"
    allure.attach(str(activity), name="current_activity", attachment_type=allure.attachment_type.TEXT)


# ---------------------------------------------------------------------------
# 例 2：Artemis 探索（消耗 token，只在必要时跑）
# ---------------------------------------------------------------------------
@allure.title("Artemis 探索：打开设置→关于手机页可正常显示")
@pytest.mark.asyncio
async def test_settings_about_exploratory(artemis):
    """探索性路径：自然语言描述，Artemis 自己找元素、点、验证。"""
    result = await artemis.explore(
        "打开设置，进入关于手机页面，确认能正常显示",
        expected_output="关于手机",
    )
    assert result.succeeded, f"Artemis 任务失败：{result.error or result.status}"
    allure.attach(str(result.output), name="artemis_output", attachment_type=allure.attachment_type.TEXT)


# ---------------------------------------------------------------------------
# 例 3：混合——Appium 断言 + Artemis 探索接力
# ---------------------------------------------------------------------------
@allure.title("混合：Appium 准备环境 → Artemis 探索 → Appium 断言结果")
@pytest.mark.asyncio
async def test_hybrid_battery_flow(driver, artemis):
    """典型分工：Appium 先把环境准备好（回到桌面），Artemis 跑探索路径，
    最后 Appium 做一次确定性断言兜底。"""
    # 1) Appium：回到桌面，保证 Artemis 从干净状态出发（零 token）
    driver.press_keycode(3)  # KEYCODE_HOME
    import time
    time.sleep(1)

    # 2) Artemis：探索电池页面，读出电量（消耗 token）
    result = await artemis.explore(
        "打开设置，进入电池页面，告诉我当前电量百分比",
        expected_output="%",
    )
    assert result.succeeded, f"Artemis 任务失败：{result.error or result.status}"

    # 3) Appium：确定性断言兜底（当前应停留在设置页，非崩溃状态）
    activity = driver.current_activity
    assert activity, "探索后应仍停留在有效 activity"
    allure.attach(str(result.output), name="battery_output", attachment_type=allure.attachment_type.TEXT)
