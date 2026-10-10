# -*- coding: utf-8 -*-
"""
Artemis 薄封装：把「探索性任务」交给 Artemis，其余交给 Appium。

分工原则（省 token 的关键）：
  - 固定流程 + 精确断言（元素存在、文本校验）→ Appium Page Object，零 token，快且稳
  - 探索性路径（找元素、自绘界面、自然语言验证）→ Artemis，用自然语言跑

用法：
    from common.artemis_client_wrapper import ArtemisWrapper
    artemis = ArtemisWrapper()
    result = await artemis.explore("打开设置，进入电池页面，告诉我当前电量")
    result.succeeded  # bool

依赖：
    pip install "artemis-client @ git+https://github.com/google/artemis.git#subdirectory=packages/artemis-client"
    # 或本地： pip install -e "D:/projects/artemis/packages/artemis-client"

前置：Artemis daemon 已起（cd D:/projects/artemis && uv run artemis ui）
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

try:
    from artemis_client import ArtemisClient, TaskResult
except ImportError:  # 没装时给一句能直接粘的提示
    raise ImportError(
        "缺少 artemis-client，先装：\n"
        '  pip install "artemis-client @ git+https://github.com/google/artemis.git'
        '#subdirectory=packages/artemis-client"\n'
        '  或本地：pip install -e "D:/projects/artemis/packages/artemis-client"'
    )


class ArtemisWrapper:
    """对 ArtemisClient 的薄封装，统一默认设备/地址/超时。"""

    def __init__(
        self,
        device_serial: str | None = None,
        base_url: str | None = None,
        default_profile: str = "flash",
        default_timeout: float = 300.0,
    ) -> None:
        self.device_serial = device_serial or os.environ.get("ARTEMIS_DEVICE")
        self.base_url = base_url or os.environ.get("ARTEMIS_BASE_URL", "http://127.0.0.1:8000")
        self.default_profile = default_profile
        self.default_timeout = default_timeout
        self._client = ArtemisClient(self.base_url, device_serial=self.device_serial)

    async def explore(
        self,
        goal: str,
        *,
        profile: str | None = None,
        timeout: float | None = None,
        expected_output: str | None = None,
    ) -> TaskResult:
        """跑一个探索性任务，返回 TaskResult（含 .succeeded / .output / .error / .turns）。"""
        result = await self._client.run(
            goal,
            profile=profile or self.default_profile,
            device_serial=self.device_serial,
            expected_output=expected_output,
            timeout=timeout or self.default_timeout,
        )
        return result

    def explore_sync(self, goal: str, **kwargs: Any) -> TaskResult:
        """同步版：给不习惯 async 的调用方（内部 asyncio.run）。"""
        return asyncio.run(self.explore(goal, **kwargs))

    async def list_devices(self):
        return await self._client.list_devices()
