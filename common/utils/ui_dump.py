"""UI 层级 dump: 把当前页面的 page_source(xml)保存到 reports/dumps 并挂到 Allure。

用途: 通用冒烟后产出的 xml 是"分析新 App 页面结构"的第一手素材
      —— 后续让 AI 根据它编写 Page Object 与业务用例。
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import allure

from common.config import config
from common.logger import logger


def dump_page(driver, name: str = "page") -> Path:
    xml = driver.page_source or ""
    dumps_dir = config.dumps_dir
    safe = re.sub(r"[^\w.-]+", "_", name).strip("_") or "page"
    path = dumps_dir / f"{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}.xml"
    path.write_text(xml, encoding="utf-8")

    node_count = len(re.findall(r"<\s?[A-Za-z]", xml))
    attr_count = xml.count("resource-id") + xml.count("accessibility")
    logger.info("[dump] 已保存 UI 层级: %s (节点≈%d)", path, node_count)

    try:
        allure.attach.file(str(path), name=f"UI_Dump_{safe}",
                           attachment_type=allure.attachment_type.XML)
    except Exception:  # noqa: BLE001
        pass

    # 附一份元素统计文本, 便于快速判断页面信息密度
    summary = {
        "file": str(path),
        "xml_size": len(xml),
        "approx_nodes": node_count,
        "ids": attr_count,
    }
    allure.attach(str(summary), name=f"UI_Summary_{safe}",
                  attachment_type=allure.attachment_type.TEXT)
    return path
