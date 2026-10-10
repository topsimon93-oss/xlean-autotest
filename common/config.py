"""全局配置中心。

读取 config/global.yaml, 并可选"深合并"config/local.yaml(设备/被测App私有信息)。
支持 CLI 覆盖(--platform/--app/--udid/--appium-server, 由 conftest 在 pytest_configure 写入)。
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

ROOT: Path = Path(__file__).resolve().parents[1]


def read_yaml(path: Path) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def _deep_merge(base: dict, override: dict) -> dict:
    """override 深合并进 base 并返回新 dict。"""
    merged = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class Config:
    _instance: "Config | None" = None

    def __init__(self, config_dir: Path | None = None) -> None:
        self.config_dir: Path = Path(config_dir) if config_dir else ROOT / "config"
        self._data: dict[str, Any] = {}
        # ---- 运行期状态(由 conftest 根据 pytest CLI 写入) ----
        self.platform: str = "android"        # android | ios
        self.app_arg: str | None = None       # --app
        self.udid: str | None = None          # --udid
        self.server_override: str | None = None
        self.app_in_use: Path | None = None   # 本次会话实际使用的 App 文件
        self.reload()

    # ---------- 单例 ----------
    @classmethod
    def instance(cls) -> "Config":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def reload(self) -> None:
        self._data = read_yaml(self.config_dir / "global.yaml")
        local = self.config_dir / "local.yaml"
        if local.exists():
            self._data = _deep_merge(self._data, read_yaml(local))

    # ---------- 通用取值 ----------
    def get(self, dotted: str, default: Any = None) -> Any:
        cur: Any = self._data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    def platform_cfg(self, platform: str | None = None) -> dict:
        """返回指定(或当前)平台的配置段, 例如 config.get('android')。"""
        name = platform or self.platform
        return dict(self._data.get(name) or {})

    # ---------- 便捷属性 ----------
    @property
    def server_url(self) -> str:
        return self.server_override or self.get("appium.server_url", "http://127.0.0.1:4723")

    @property
    def implicit_wait(self) -> int:
        return int(self.get("wait.implicit", 10))

    @property
    def explicit_wait(self) -> int:
        return int(self.get("wait.explicit", 20))

    @property
    def poll_frequency(self) -> float:
        return float(self.get("wait.poll_frequency", 0.5))

    @property
    def launch_settle(self) -> int:
        return int(self.get("wait.launch_settle", 3))

    @property
    def screenshots_dir(self) -> Path:
        p = ROOT / str(self.get("report.screenshots_dir", "screenshots"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def dumps_dir(self) -> Path:
        p = ROOT / str(self.get("report.dumps_dir", "reports/dumps"))
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---------- CLI 覆盖 ----------
    def set_cli(self, platform: str | None = None, app: str | None = None,
                udid: str | None = None, server: str | None = None) -> None:
        if platform:
            self.platform = platform.lower()
        if app:
            self.app_arg = str(app)
        if udid:
            self.udid = str(udid)
        if server:
            self.server_override = str(server)

    # ---------- App 解析 ----------
    def resolve_app_path(self) -> Path | None:
        """优先级: --app 指定路径 > 自动扫描 apps/ 目录下**最新**的匹配安装包。

        按修改时间取最新, 这样"把新版 apk 扔进 apps/ 覆盖旧版"后无需改任何参数。
        """
        if self.app_arg:
            p = Path(self.app_arg)
            if not p.is_absolute():
                p = ROOT / p
            if p.exists():
                return p.resolve()

        ext_key = "apk_dir" if self.platform == "android" else "ipa_dir"
        folder = ROOT / str(self.get(f"app_paths.{ext_key}", "apps"))
        exts = {".apk"} if self.platform == "android" else {".ipa", ".app"}
        if folder.exists():
            candidates = [f for f in folder.iterdir() if f.is_file()
                          and f.suffix.lower() in exts]
            if candidates:
                return max(candidates, key=lambda f: f.stat().st_mtime).resolve()
        return None


# 模块级单例, 业务代码统一 `from common.config import config` 使用
config = Config.instance()
