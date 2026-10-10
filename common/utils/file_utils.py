"""通用文件/路径工具。"""
from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
