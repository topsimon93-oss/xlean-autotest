"""全局 conftest: 平台/App/设备参数解析、平台自动跳过、Appium 会话 fixture、
失败自动截图、Allure 环境信息。"""
from __future__ import annotations

import os
import platform as _sys_platform
from pathlib import Path

import pytest

# 本机代理(HTTP_PROXY/梯子)会劫持发往 127.0.0.1 的请求: 代理转发时把请求行
# 改写成绝对 URL, 导致 Appium 服务端的免代理(NO_PROXY)名单全部失配,
# 命令被裸代理到手机端 uiautomator2 server 而报 UnknownMethodException/404。
# 所以凡是发往本机 Appium/服务的请求必须直连。
_NO_PROXY = "127.0.0.1,localhost"
os.environ.setdefault("NO_PROXY", _NO_PROXY)
os.environ.setdefault("no_proxy", _NO_PROXY)

from common.config import Config, config
from common.driver_manager import DriverManager
from common.logger import logger


def pytest_addoption(parser):
    group = parser.getgroup("appautotest", "AppAutoTest 双端 App 自动化")
    group.addoption("--platform", action="store", default=None,
                    choices=["android", "ios"],
                    help="运行平台: android | ios (默认 android)")
    group.addoption("--app", action="store", default=None,
                    help="待测 App 路径(*.apk/*.ipa/*.app), 相对根目录或绝对路径; 缺省自动扫 apps/")
    group.addoption("--udid", action="store", default=None,
                    help="设备 udid; Android 缺省自动探测 adb 第一个设备")
    group.addoption("--appium-server", action="store", default=None,
                    help="Appium Server 地址, 覆盖配置文件")
    group.addoption("--with-demo", action="store_true",
                    help="运行 demo 示例用例(默认排除)")


def pytest_configure(config):
    c = Config.instance()
    c.set_cli(platform=config.getoption("--platform") or "android",
              app=config.getoption("--app"),
              udid=config.getoption("--udid"),
              server=config.getoption("--appium-server"))
    config._app_platform = c.platform
    logger.info("运行平台: %s", c.platform.upper())


def pytest_collection_modifyitems(session, config, items):
    """平台隔离 + demo 默认排除, 保证任意平台上跑全套命令都不报错。"""
    plat = config._app_platform
    with_demo = config.getoption("--with-demo")

    def _skip(reason: str):
        return pytest.mark.skip(reason=reason)

    for item in items:
        names = {m.name for m in item.iter_markers()}
        if "demo" in names and not with_demo:
            item.add_marker(_skip("示例用例, 需加 --with-demo 执行"))
            continue
        if "android" in names and plat != "android":
            item.add_marker(_skip(f"当前平台 {plat}, 该用例仅 Android"))
        elif "ios" in names and plat != "ios":
            item.add_marker(_skip(f"当前平台 {plat}, 该用例仅 iOS(macOS+Xcode)"))
        elif plat == "android" and "ios" in names:
            item.add_marker(_skip("该用例仅 iOS"))


# ---------------- fixtures ----------------
@pytest.fixture(scope="session")
def driver():
    """Appium 会话(整个 session 复用一次)。teardown 自动退出。

    平台守卫: iOS 会话强依赖 macOS + Xcode, 在 Windows/Linux 上直接 skip,
    保证"跑到不支持平台"也不会红, Android 不受影响。
    """
    c = Config.instance()
    if c.platform == "ios" and _sys_platform.system() != "Darwin":
        pytest.skip("iOS 会话需要 macOS + Xcode(XCUITest); 当前系统为 "
                    f"{_sys_platform.system()}, 该用例自动跳过。"
                    "用例骨架可在 Windows 上开发维护, 到 Mac/CI 上执行。")

    app_path = c.resolve_app_path()
    if app_path:
        logger.info("[会话] 将安装并启动待测 App: %s", app_path)
    else:
        logger.info("[会话] 未找到 App 文件, 将直接启动配置中的已安装应用 "
                    "(android=%s / ios=%s)", c.get("android.app_package"),
                    c.get("ios.bundle_id"))
    d = DriverManager.create_driver(platform=c.platform, app_path=app_path,
                                    udid=c.udid, server_url=c.server_url)
    c.app_in_use = app_path
    yield d
    DriverManager.quit()


# ---------------- 每条用例结束自动截图(证据) + 失败自动截图 ----------------
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """两条证据线:
    1. 每条用例 call 阶段结束都截图, 命名 case_{用例名} —— 供全流程报告的
       「证据截图」列按用例名取图(实测: 报告解析 junitxml 只有函数名,
       所以截图命名必须直接用函数名, 中文 desc 只进 Allure)。
    2. 失败时额外存 FAILED_{用例名}(与 case_ 图并存, 排查更直观)。
    均不阻断报告生成。
    """
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    driver = item.funcargs.get("driver")
    if driver is None:
        return
    from common.utils.allure_utils import attach_screenshot
    attach_screenshot(driver, f"case_{item.name}")
    if report.failed:
        attach_screenshot(driver, f"FAILED_{item.name}")
        logger.warning("[失败] %s 已自动截图并挂到 Allure", item.name)


def pytest_sessionfinish(session, exitstatus):
    """把本次运行环境写入 allure-results/environment.properties, 报告中可见。"""
    try:
        c = Config.instance()
        out = session.config.getoption("--alluredir") or "allure-results"
        dir_path = Path(str(out))  # 兼容 pytest 的 py.path 对象
        if not dir_path.is_absolute():
            dir_path = Path(str(session.config.rootdir)) / dir_path
        dir_path.mkdir(parents=True, exist_ok=True)
        app_label = c.app_arg or (str(c.app_in_use) if c.app_in_use else "已安装配置包")
        lines = [
            f"platform={c.platform}",
            f"app={app_label}",
            f"appium_server={c.server_url}",
            f"udid={c.udid or 'auto'}",
            f"os={_sys_platform.system()}",
            f"python={_sys_platform.python_version()}",
        ]
        (dir_path / "environment.properties").write_text(
            "\n".join(lines), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.debug("写 environment.properties 失败(忽略): %s", exc)


# ---------------- 其它 fixture ----------------
@pytest.fixture(scope="session")
def platform() -> str:
    return config.platform


@pytest.fixture
def settle_seconds() -> int:
    """App 启动后等待首屏稳定的时长(秒)。"""
    return int(config.launch_settle)
