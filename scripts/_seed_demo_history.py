# -*- coding: utf-8 -*-
"""临时脚本：造几组演示历史数据，让趋势页有起伏可看。
跑完即弃，不影响正式 history.json（会备份到 history.real.json）。
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run_full_pipeline as r  # noqa: E402

NAMES = list(r.CASE_TITLES.keys())

# 模拟 6 次运行：通过率从差到好，含几次失败，耗时波动
DEMO = [
    # (ts, cases 状态序列, 每条耗时基数)
    ("2026-10-07 09:12", ["PASS"] * 10 + ["FAIL", "FAIL", "ERROR"], 55),
    ("2026-10-07 14:30", ["PASS"] * 11 + ["FAIL", "ERROR"], 50),
    ("2026-10-08 10:05", ["PASS"] * 12 + ["FAIL"], 72),
    ("2026-10-08 18:20", ["PASS"] * 13, 80),
    ("2026-10-09 15:57", ["PASS"] * 13, 78),
    ("2026-10-09 20:20", ["PASS"] * 13, 60),
]

history = []
for ts, statuses, base in DEMO:
    cases = []
    for i, name in enumerate(NAMES):
        st = statuses[i] if i < len(statuses) else "PASS"
        # 让某些用例耗时明显偏高（邮箱、计划页）
        if name in ("test_account_email_format", "test_plan_tab_placeholder"):
            t = round(base * 1.8 + 8, 2)
        elif st != "PASS":
            t = round(base * 0.9, 2)
        else:
            t = round(base + (i % 5) * 3, 2)
        cases.append({"name": name, "time": t, "status": st})
    passed = sum(1 for c in cases if c["status"] == "PASS")
    failed = sum(1 for c in cases if c["status"] in ("FAIL", "ERROR"))
    elapsed = round(sum(c["time"] for c in cases), 2)
    history.append({"ts": ts, "total": len(cases), "passed": passed,
                    "failed": failed, "elapsed": elapsed, "cases": cases})

# 备份真实历史（只有 1 条）——已备份过就跳过
real = r.HISTORY_FILE
bak = Path(str(real) + ".real")
if real.exists() and not bak.exists():
    real.rename(bak)

r.HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2),
                          encoding="utf-8")
t = r.write_trend()
print("演示历史已写入，趋势页:", t)
