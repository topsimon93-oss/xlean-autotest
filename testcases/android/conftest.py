"""Android 用例目录级 conftest: 每条用例 = adb 冷启动 + 全新 Appium 会话。

为什么这么做(实测踩坑, 两个大坑):
  坑 1: 会话级 driver 复用 + fixture 里 terminate_app/activate_app 冷启动,
        会弄脏 uiautomator2 的仪器连接 —— 之后页面上明明存在的元素(如账号页
        异步加载的邮箱值), find 静默返回空, 换全新会话立刻能找到。
  坑 2: noReset 下新会话不会重启 App, 而是原样恢复上一次的画面 ——
        上一条用例停在深层页面, 下一条就起点不对。
  方案: 每条用例先在 adb 层 force-stop + am start(此时还没有 Appium 会话,
        随便杀), 再建全新会话 —— 会话内全程不杀 App。
"""
from __future__ import annotations

import platform as _sys_platform
import subprocess
import time

import pytest

from common.config import Config
from common.driver_manager import DriverManager
from common.logger import logger


def _adb_cold_start(cfg: Config) -> None:
    """adb 层冷启动 App 到入口页(必须在会话创建之前, 会话内杀 App 会弄脏连接)。"""
    pkg = cfg.get("android.app_package")
    act = cfg.get("android.app_activity")
    if not pkg or not act:
        return
    base = ["adb"]
    if cfg.udid:
        base += ["-s", str(cfg.udid)]
    try:
        subprocess.run(base + ["shell", "am", "force-stop", pkg],
                       capture_output=True, timeout=15)
        time.sleep(1)
        subprocess.run(base + ["shell", "am", "start", "-n", f"{pkg}/{act}"],
                       capture_output=True, timeout=15)
        time.sleep(2)  # 等首屏渲染(原4s过保守; 会话建立后 is_visible 有隐式等待兜底)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[会话] adb 冷启动失败(忽略, 由会话自行拉起): %s", exc)


def _wait_server_release(cfg: Config) -> None:
    """teardown 后给 Appium server 时间释放 session/instrumentation, 并清残留端口转发。

    Appium 2 的 uiautomator2 会话关闭是异步的(DELETE /session 后 instrumentation
    还要几秒才 stop); 立即建下一条会话会撞车导致 instrumentation 崩。
    """
    time.sleep(2)
    udid = str(cfg.udid) if cfg.udid else None
    base = ["adb"]
    if udid:
        base += ["-s", udid]
    try:
        # 列出并清掉 uiautomator2 遗留的端口转发(报 tcp:82xx not found 的来源)
        out = subprocess.run(base + ["forward", "--list"],
                             capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[0] == udid and "tcp:82" in parts[1]:
                subprocess.run(base + ["forward", "--remove", parts[1]],
                               capture_output=True, timeout=10)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[会话] 清理端口转发失败(忽略): %s", exc)


@pytest.fixture
def driver():
    """Appium 会话(每条用例独立: 先 adb 冷启动, 再建会话)。iOS 守卫同上级。"""
    c = Config.instance()
    if c.platform == "ios" and _sys_platform.system() != "Darwin":
        pytest.skip("iOS 会话需要 macOS + Xcode(XCUITest); 当前系统为 "
                    f"{_sys_platform.system()}, 该用例自动跳过。")
    app_path = c.resolve_app_path()
    if app_path:
        logger.info("[会话] 将安装并启动待测 App: %s", app_path)
    else:
        # 没有安装包场景: 先 adb 冷启动到入口页, 再建会话(顺序不能反)
        _adb_cold_start(c)
        logger.info("[会话] adb 冷启动完成, 建会话直连 (android=%s)",
                    c.get("android.app_package"))
    d = DriverManager.create_driver(platform=c.platform, app_path=app_path,
                                    udid=c.udid, server_url=c.server_url)
    c.app_in_use = app_path
    yield d
    DriverManager.quit()
    # teardown 后必须等 Appium server 真正释放 instrumentation 再进入下一条,
    # 否则下一条冷启动建会话会与上一条未删干净的 session 撞车, 把 uiautomator2 挤崩
    # (症状: 第 1 条 PASSED, 第 2 条起连续 ERROR "instrumentation process is not running")。
    _wait_server_release(c)
