"""根级 conftest: 仅负责把项目根目录加入 sys.path, 保证 common/pages 可直接 import。

注意: 真正的 pytest 配置(driver 会话、--platform 等参数)在 testcases/conftest.py。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
