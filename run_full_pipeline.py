# -*- coding: utf-8 -*-
"""
一键全流程：Appium 回归 + Artemis 探索 分工编排。

流程：
  1. 跑 Appium 回归（pytest，零 token，固定断言）
  2. 跑 Artemis 探索（消耗 token，自然语言验证）
  3. 汇总两份结果，生成总报告（含每条用例明细 + 截图）

用法：
  python run_full_pipeline.py                      # 全流程
  python run_full_pipeline.py --skip-appium        # 只跑 Artemis 探索
  python run_full_pipeline.py --skip-artemis       # 只跑 Appium 回归
  python run_full_pipeline.py --report-only        # 不跑任何东西，用上次数据重新出报告

前置：
  - Appium Server 已起（http://127.0.0.1:4723）
  - Artemis daemon 已起（cd D:/projects/artemis && uv run artemis ui）
  - 真机已连：adb devices 能看到 device
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import datetime as dt
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent  # AppAutoTest 根目录（脚本就放在根下）
ROOT = HERE

# Artemis suite 目录（独立于 AppAutoTest，本机已搭好）
ARTEMIS_SUITE = Path("C:/Users/xlean/WorkBuddy/2026-10-06-10-05-46/artemis-suite")
ARTEMIS_RUNNER = ARTEMIS_SUITE / "runner.py"
ARTEMIS_PY = Path("C:/Users/xlean/.workbuddy/binaries/python/envs/artemis-suite/Scripts/python.exe")

REPORT_DIR = HERE / "reports" / "pipeline"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
JUNIT_XML = REPORT_DIR / "appium_junit.xml"          # pytest 每次跑完落盘
ARTEMIS_SNAPSHOT = REPORT_DIR / "artemis_results.json"  # 每次跑完快照，防被下次运行覆盖
HISTORY_FILE = REPORT_DIR / "history.json"           # 历史运行记录（趋势页数据源，追加不覆盖）
TREND_HTML = REPORT_DIR / "trend.html"               # 结果对比/趋势交互面板

# AppAutoTest 自己的 .venv（pytest/appium 都装在这里；必须用它跑回归）
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"


def _venv_python() -> str:
    return str(VENV_PY if VENV_PY.exists() else Path(sys.executable))


def parse_junit(path: Path) -> list[dict]:
    """解析 pytest 的 junitxml，返回每条用例的明细。"""
    if not path.exists():
        return []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []
    cases = []
    for tc in root.iter("testcase"):
        status, msg = "PASS", ""
        for tag, label in (("failure", "FAIL"), ("error", "ERROR"), ("skipped", "SKIP")):
            node = tc.find(tag)
            if node is not None:
                status = label
                msg = (node.get("message") or "")[:300]
        cases.append({
            "name": tc.get("name") or "?",
            "file": tc.get("classname") or "",
            "time": round(float(tc.get("time") or 0), 2),
            "status": status,
            "message": msg,
        })
    return cases


def load_artemis_tasks() -> list[dict]:
    """读 Artemis 任务明细（优先用快照，其次 runner 自己的 results.json）。"""
    for p in (ARTEMIS_SNAPSHOT, ARTEMIS_SUITE / "results" / "results.json"):
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except Exception:
                pass
    return []


def record_history(cases: list[dict]) -> None:
    """把本次 Appium 回归结果追加进历史库（趋势页数据源，只增不删）。

    每次运行存一条 record：
      {ts, total, passed, failed, elapsed, cases:[{name, time, status}]}
    """
    if not cases:
        return
    now = dt.datetime.now()
    passed = sum(1 for c in cases if c["status"] == "PASS")
    failed = sum(1 for c in cases if c["status"] in ("FAIL", "ERROR"))
    elapsed = round(sum(c.get("time", 0) for c in cases), 2)
    record = {
        "ts": now.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "elapsed": elapsed,
        "cases": [{"name": c["name"], "time": c.get("time", 0), "status": c["status"]}
                  for c in cases],
    }
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if not isinstance(history, list):
                history = []
        except Exception:
            history = []
    history.append(record)
    # 只保留最近 60 次，避免无限膨胀
    history = history[-60:]
    try:
        HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2),
                                encoding="utf-8")
        print(f"[历史] 已记录本次运行 -> {HISTORY_FILE.name}（累计 {len(history)} 次）")
    except Exception as e:
        print(f"[!] 历史落盘失败：{e}")




def run_appium_regression() -> dict:
    """跑 Appium 回归（xLean 13 条用例，零 token），解析 junitxml 返回结果。

    返回：{"status", "passed", "total", "cases", "ran_this_time", "detail"}
    """
    print("=" * 60)
    print("① Appium 回归测试（xLean，零 token）")
    print("=" * 60)

    # 让路：pytest.ini 的 --clean-alluredir 会 rmtree 清空 allure-results，
    # 触发 WorkBuddy 安全防护拦截（SystemExit）。先改名旧的，让 allure 新建空目录。
    allure_dir = ROOT / "allure-results"
    if allure_dir.exists():
        try:
            alt = ROOT / f"allure-results_bak_{dt.datetime.now():%Y%m%d_%H%M%S}"
            allure_dir.rename(alt)
            print(f"  [让路] 旧 allure-results 已改名 -> {alt.name}")
        except Exception as e:
            print(f"  [!] allure-results 改名失败（忽略继续）：{e}")

    test_files = [
        "testcases/android/test_xlean_app.py",
        "testcases/android/test_xlean_settings_account.py",
    ]
    # -v 详细模式：每条用例名 + PASSED/FAILED 实时打印；-p no:cacheprovider 避免缓存噪音
    cmd = [str(_venv_python()), "-m", "pytest", *test_files,
           "--platform", "android",
           f"--junitxml={JUNIT_XML}", "-v", "-p", "no:cacheprovider"]
    print("  执行:", " ".join(cmd))
    print("  ─────────────────────────────────────────────")
    print("  实时进度：每条用例跑完会打印 ✓ 或 ✗，约 15-20 分钟")
    print("  ─────────────────────────────────────────────")

    # 流式执行：pytest 输出重定向到临时文件（而非管道）。
    # 关键修复：管道模式下，pytest 虽退出但其孙进程(uiautomator2 driver 线程)
    # 继承了 stdout 写端不释放，导致 `for line in pipe` 永远等不到 EOF -> 报告阶段卡死。
    # 改用文件 + start_new_session，pytest 退出即 EOF，进度用 tail 增量读取实时打印。
    tmp_out = REPORT_DIR / f"_pytest_live_{dt.datetime.now():%Y%m%d_%H%M%S}.log"
    stdout_lines: list[str] = []
    try:
        with open(tmp_out, "w", encoding="utf-8", errors="replace") as fout:
            proc = subprocess.Popen(cmd, cwd=str(ROOT),
                                    stdout=fout, stderr=subprocess.STDOUT,
                                    start_new_session=True)
            # 增量 tail：只读新写入的内容，实时打印关键行
            seen = 0
            while proc.poll() is None:
                try:
                    with open(tmp_out, "r", encoding="utf-8", errors="replace") as fin:
                        fin.seek(seen)
                        for line in fin:
                            line = line.rstrip("\n")
                            if line:
                                stdout_lines.append(line)
                                if any(k in line for k in ("PASSED", "FAILED", "ERROR", "passed", "failed", "error", "====")):
                                    print("  " + line, flush=True)
                        seen = fin.tell()
                except FileNotFoundError:
                    pass
                time.sleep(0.5)
            # 收尾：读最后残留
            try:
                with open(tmp_out, "r", encoding="utf-8", errors="replace") as fin:
                    fin.seek(seen)
                    for line in fin:
                        line = line.rstrip("\n")
                        if line:
                            stdout_lines.append(line)
                            if any(k in line for k in ("PASSED", "FAILED", "ERROR", "passed", "failed", "error", "====")):
                                print("  " + line, flush=True)
            except FileNotFoundError:
                pass
    finally:
        try:
            tmp_out.unlink(missing_ok=True)
        except Exception:
            pass

    detail = "\n".join(stdout_lines)[-2000:]
    cases = parse_junit(JUNIT_XML)
    passed = sum(1 for c in cases if c["status"] == "PASS")
    total = len(cases)
    status = "PASS" if (total > 0 and passed == total) else ("FAIL" if total else "ERROR")
    print("  ─────────────────────────────────────────────")
    print(f"  Appium 回归结果：{passed}/{total} 通过")
    return {"status": status, "passed": passed, "total": total,
            "detail": detail, "cases": cases, "ran_this_time": total > 0}


def run_artemis_explore() -> dict:
    """跑 Artemis 探索，返回结构化结果（含每任务明细），并快照防覆盖。"""
    print("=" * 60)
    print("② Artemis 探索测试（消耗 token，自然语言验证）")
    print("=" * 60)
    if not ARTEMIS_RUNNER.exists():
        return {"status": "SKIP", "detail": f"找不到 {ARTEMIS_RUNNER}", "tasks": []}
    if not ARTEMIS_PY.exists():
        return {"status": "SKIP", "detail": "找不到 Artemis 隔离 Python 环境", "tasks": []}
    cmd = [str(ARTEMIS_PY), str(ARTEMIS_RUNNER)]
    print("  执行:", " ".join(cmd))
    try:
        proc = subprocess.run(cmd, cwd=ARTEMIS_SUITE, capture_output=True, text=True, timeout=3600)
    except subprocess.TimeoutExpired:
        tasks = load_artemis_tasks()
        return {"status": "ERROR", "detail": "Artemis 探索超时", "tasks": tasks}

    tasks = load_artemis_tasks()
    # 快照：runner 每次运行会覆盖自己的 results.json，这里存一份供 --report-only 用
    if tasks:
        try:
            ARTEMIS_SNAPSHOT.write_text(json.dumps(tasks, ensure_ascii=False, indent=2),
                                        encoding="utf-8")
        except Exception:
            pass
    passed = sum(1 for r in tasks if r.get("ok"))
    total = len(tasks)
    detail = (proc.stdout or "")[-2000:]
    status = "PASS" if (total > 0 and passed == total) else "FAIL"
    if not total:
        status = "FAIL" if proc.returncode != 0 else "PASS"
    return {"status": status, "passed": passed, "total": total,
            "detail": detail, "tasks": tasks, "ran_this_time": True}


def _esc(s: str) -> str:
    return (s or "").replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


def _img_uri(p: str | None) -> str | None:
    """把截图读成 base64 data URI，嵌进 HTML（报告自包含，发谁都直接能看）。"""
    if not p:
        return None
    try:
        data = Path(p).read_bytes()
        return "data:image/png;base64," + base64.b64encode(data).decode()
    except Exception:
        return None


# 每条用例结束的自动截图（conftest.py 钩子产出），按用例名取最新一张作证据
SCREENSHOT_DIR = ROOT / "screenshots"


_SHOT_INDEX: dict[str, list[Path]] | None = None


def _build_shot_index() -> dict[str, list[Path]]:
    """一次性扫描 screenshots 建索引 {case_name: [按 mtime 升序的路径]}，避免每条用例重复全量 glob。"""
    global _SHOT_INDEX
    if _SHOT_INDEX is not None:
        return _SHOT_INDEX
    import re as _re
    _tmp: dict[str, list[Path]] = {}
    if SCREENSHOT_DIR.exists():
        # case_{name}_{YYYYmmdd}_{HHMMSS}_{ms}.png -> 按 name 归组
        for p in SCREENSHOT_DIR.glob("case_*_*.png"):
            m = _re.match(r"case_(.+)_(\d{8})_(\d{6})_(\d+)\.png$", p.name)
            if m:
                _tmp.setdefault(m.group(1), []).append(p)
    for v in _tmp.values():
        v.sort(key=lambda x: x.stat().st_mtime)
    _SHOT_INDEX = _tmp
    return _SHOT_INDEX


def _case_shot(name: str) -> str | None:
    """按用例名找最新的 case_{name}_*.png 截图，转 data URI。"""
    if not SCREENSHOT_DIR.exists():
        return None
    idx = _build_shot_index()
    candidates = idx.get(name)
    return _img_uri(str(candidates[-1])) if candidates else None


# 用例函数名 -> 人话说明（报告里展示中文，函数名作小字备注）
CASE_TITLES = {
    "test_app_launch_settles": "App 启动后首屏稳定",
    "test_home_screen_renders": "xLean 首页正常渲染（设备名/入口/临时清洁卡片都在）",
    "test_battery_percent_format": "设备电量显示为合法百分比",
    "test_clean_status_card": "清洁状态卡片存在",
    "test_plan_tab_placeholder": "「计划」页显示敬请期待",
    "test_explore_tab_placeholder": "「探索」页显示敬请期待",
    "test_menu_open_close": "抽屉菜单能打开、返回键能收起",
    # xLean 设备设置页 + 账号信息页（6 条）
    "test_settings_page_opens": "设备设置页能打开（清洁设置/设备控制/设备管理三组齐全）",
    "test_settings_entries_present": "设备设置页 10 个入口全部显示（含滚动到底）",
    "test_settings_back_to_home": "设备设置页按返回能回首页",
    "test_account_page_opens": "账号信息页能打开（账号/邮箱/管理区齐全）",
    "test_account_email_format": "账号邮箱格式合法",
    "test_account_danger_buttons_exist": "退出登录/注销账号按钮存在（只看不点）",
}


def _case_title(name: str) -> str:
    return CASE_TITLES.get(name, name)


def _fmt_secs(s) -> str:
    """秒数转人话：36 秒 / 5 分 25 秒。"""
    if s is None:
        return "—"
    s = round(float(s))
    if s < 60:
        return f"{s} 秒"
    return f"{s // 60} 分 {s % 60} 秒"


def _status_badge(s: str) -> str:
    m = {"PASS": ("✅", "#16a34a", "通过"), "FAIL": ("❌", "#dc2626", "失败"),
         "SKIP": ("⏭️", "#9ca3af", "跳过"), "ERROR": ("❌", "#dc2626", "异常")}
    icon, color, label = m.get(s, ("•", "#888", s))
    return f'<span style="color:{color};font-weight:700">{icon} {label}</span>'


def _stat_card(title: str, value: str, sub: str, color: str) -> str:
    return (f'<div class="stat" style="border-top:3px solid {color}">'
            f'<div class="stat-v" style="color:{color}">{value}</div>'
            f'<div class="stat-t">{title}</div><div class="stat-s">{sub}</div></div>')


def write_summary(appium: dict, artemis: dict) -> Path:
    """生成总报告：汇总卡片 + 每条用例明细 + Artemis 截图。"""
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cases = appium.get("cases") or []
    tasks = artemis.get("tasks") or []
    appium_pass = sum(1 for c in cases if c["status"] == "PASS")
    artemis_pass = sum(1 for t in tasks if t.get("ok"))
    appium_time = round(sum(c.get("time", 0) for c in cases), 1)
    artemis_time = round(sum(t.get("elapsed", 0) or 0 for t in tasks), 1)

    has_fail = any(c["status"] in ("FAIL", "ERROR") for c in cases) or \
               any(t.get("ok") is False for t in tasks) or \
               appium.get("status") in ("FAIL", "ERROR") or artemis.get("status") in ("FAIL", "ERROR")
    n_fail = sum(1 for c in cases if c["status"] in ("FAIL", "ERROR")) + \
             sum(1 for t in tasks if t.get("ok") is False)
    n_total = len(cases) + len(tasks)
    overall_color = "#dc2626" if has_fail else "#16a34a"
    if n_total == 0:
        overall_text = "本次没有运行任何测试"
    elif has_fail:
        overall_text = f"❌ {n_fail} 条测试失败，需要处理"
    else:
        overall_text = f"✅ 全部 {n_total} 条测试通过"

    # —— Appium 明细表（中文标题为主，函数名退居小字，带证据截图） ——
    if cases:
        rows = ""
        for c in cases:
            note = f'<div class="failmsg">{_esc(c["message"])}</div>' if c["message"] else ""
            uri = _case_shot(c["name"])
            shot = (f'<img src="{uri}" class="thumb" alt="截图" onclick="showImg(this.src)">'
                    if uri else '<span class="noshot">无截图</span>')
            rows += (f'<tr><td><b>{_esc(_case_title(c["name"]))}</b>'
                     f'<div class="rawname">{_esc(c["name"])}</div>{note}</td>'
                     f'<td class="num">{_fmt_secs(c["time"])}</td>'
                     f'<td>{_status_badge(c["status"])}</td>'
                     f'<td class="shot">{shot}</td></tr>')
        appium_table = (f'<table><tr><th>测试内容</th><th>耗时</th><th>结果</th><th>证据截图</th></tr>'
                        f'{rows}</table>'
                        f'<div class="note">点缩略图看大图 · 来源：{"本次实跑" if appium.get("ran_this_time") else "上次运行留档"}</div>')
    else:
        appium_table = f'<pre>{_esc(appium.get("detail") or "无数据")}</pre>'

    # —— Artemis 明细表（带截图） ——
    if tasks:
        rows = ""
        for t in tasks:
            ok = t.get("ok")
            st = "PASS" if ok else ("SKIP" if t.get("status") == "SKIP" else "FAIL")
            uri = _img_uri(t.get("screenshot"))
            # 注意：不能用 <a href="data:...">，浏览器禁止顶层导航到 data URI（点了没反应）。
            # 用 JS 灯箱：点缩略图原地放大，点任意处关闭。
            shot = (f'<img src="{uri}" class="thumb" alt="截图" onclick="showImg(this.src)">'
                    if uri else '<span class="noshot">无截图</span>')
            err = t.get("error") or ""
            note = f'<div class="failmsg">{_esc(err)}</div>' if (err and not ok) else ""
            rows += (f'<tr><td><b>{_esc(t.get("name"))}</b>'
                     f'<div class="goal">{_esc(t.get("goal"))}</div>{note}</td>'
                     f'<td class="num">{_fmt_secs(t.get("elapsed"))}</td>'
                     f'<td>{_status_badge(st)}</td>'
                     f'<td class="shot">{shot}</td></tr>')
        artemis_table = (f'<table><tr><th>让 AI 做的事</th><th>耗时</th><th>结果</th><th>证据截图</th></tr>'
                         f'{rows}</table>'
                         f'<div class="note">点缩略图看大图 · '
                         f'来源：{"本次实跑" if artemis.get("ran_this_time") else "上次运行留档"}</div>')
    else:
        artemis_table = f'<pre>{_esc(artemis.get("detail") or "无数据")}</pre>'

    skipped_note_appium = "" if appium.get("ran_this_time") else '<div class="note">⏭️ 本次未跑，显示上次数据</div>'
    skipped_note_artemis = "" if artemis.get("ran_this_time") else '<div class="note">⏭️ 本次未跑，显示上次数据</div>'

    html = f"""<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>全流程测试报告</title>
<style>
body{{font-family:-apple-system,"Microsoft YaHei",sans-serif;margin:0;background:#f5f5f7;color:#1d1d1f}}
.wrap{{max-width:980px;margin:0 auto;padding:32px}}
h1{{font-size:24px;margin:0 0 4px}}
.sub{{color:#6e6e73;font-size:13px;margin-bottom:16px}}
.verdict{{padding:14px 20px;border-radius:12px;color:#fff;font-size:16px;font-weight:700;margin-bottom:20px;background:{overall_color}}}
.stats{{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}}
.stat{{flex:1;min-width:180px;background:#fff;border-radius:12px;padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.stat-v{{font-size:22px;font-weight:800}}
.stat-t{{font-size:13px;color:#3c3c43;margin-top:2px}}
.stat-s{{font-size:12px;color:#6e6e73;margin-top:2px}}
.card{{background:#fff;border-radius:12px;padding:20px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.06)}}
.card h2{{margin:0 0 8px;font-size:18px}}
.card .meta{{color:#6e6e73;font-size:13px;margin-bottom:8px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;color:#6e6e73;font-weight:600;padding:8px 10px;border-bottom:2px solid #eee}}
td{{padding:10px;border-bottom:1px solid #f0f0f0;vertical-align:top}}
.num{{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums}}
.mono{{font-family:Consolas,monospace;font-size:12px}}
.rawname{{color:#a1a1a6;font-size:11px;font-family:Consolas,monospace;margin-top:2px}}
.goal{{color:#6e6e73;font-size:12px;margin-top:2px;max-width:420px}}
.thumb{{max-width:150px;max-height:120px;border-radius:6px;border:1px solid #e5e5ea;display:block;cursor:zoom-in}}
#lightbox{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.86);z-index:99;align-items:center;justify-content:center;cursor:zoom-out}}
#lightbox img{{max-width:94vw;max-height:94vh;border-radius:8px;box-shadow:0 8px 40px rgba(0,0,0,.5)}}
.shot{{width:160px}}
.noshot{{color:#c7c7cc;font-size:12px}}
.note{{color:#6e6e73;font-size:12px;margin-top:8px}}
.failmsg{{color:#dc2626;font-size:12px;margin-top:4px;white-space:pre-wrap}}
pre{{background:#fafafa;padding:12px;border-radius:8px;font-size:12px;overflow-x:auto;white-space:pre-wrap}}
details summary{{cursor:pointer;color:#007aff;font-size:13px;margin-top:8px}}
</style></head><body><div class="wrap">
<h1>Appium 回归 + Artemis 探索 全流程报告</h1>
<div class="sub">生成时间 {now}</div>
<div class="verdict">{overall_text}</div>
<div id="lightbox" onclick="this.style.display='none'"><img id="lb-img" alt="大图"></div>
<script>
function showImg(src){{var lb=document.getElementById('lightbox');document.getElementById('lb-img').src=src;lb.style.display='flex';}}
</script>

<div class="stats">
{_stat_card("Appium 自动回归", f"{appium_pass}/{len(cases)} 通过", f"耗时 {_fmt_secs(appium_time)} · 不花钱", "#0a84ff" if appium.get("status")=="PASS" else ("#dc2626" if appium.get("status") in ("FAIL","ERROR") else "#9ca3af"))}
{_stat_card("Artemis AI 探索", f"{artemis_pass}/{len(tasks)} 通过", f"耗时 {_fmt_secs(artemis_time)} · 花 token", "#16a34a" if artemis.get("status")=="PASS" else ("#dc2626" if artemis.get("status") in ("FAIL","ERROR") else "#9ca3af"))}
{_stat_card("总计", f"{n_total} 条", f"失败 {n_fail} 条" + ("，全过！" if n_total and not has_fail else ""), "#1d1d1f")}
{_stat_card("总耗时", _fmt_secs(appium_time + artemis_time), f"其中 AI 探索占 {_fmt_secs(artemis_time)}", "#ff9f0a")}
</div>

<div class="card"><h2>① Appium 自动回归 {_status_badge(appium.get("status","SKIP"))}</h2>
<div class="meta">固定脚本自动点、自动检查 · 这部分不花钱</div>
{skipped_note_appium}
{appium_table}
<details><summary>原始输出（给排查用，平时不用看）</summary><pre>{_esc(appium.get("detail") or "")}</pre></details></div>

<div class="card"><h2>② Artemis AI 探索 {_status_badge(artemis.get("status","SKIP"))}</h2>
<div class="meta">AI 看着屏幕替你操作手机并验证 · 这部分花 token（很便宜）</div>
{skipped_note_artemis}
{artemis_table}
<details><summary>原始输出（给排查用，平时不用看）</summary><pre>{_esc(artemis.get("detail") or "")}</pre></details></div>

<div class="card"><h2>两类测试怎么分工</h2>
<div class="meta">省钱的关键：脚本能干的别让 AI 干</div>
<pre>固定流程、点按钮、检查文字 → Appium 脚本（不花钱，几秒一条）
需要「看着屏幕找东西」的探索 → Artemis AI（花 token，少量用）</pre></div>
</div></body></html>"""

    path = REPORT_DIR / "pipeline_report.html"
    path.write_text(html, encoding="utf-8")
    return path


def write_trend() -> Path | None:
    """生成交互式结果对比/趋势面板（读 history.json）。

    没有历史数据时不生成，返回 None。
    """
    if not HISTORY_FILE.exists():
        return None
    try:
        history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(history, list) or not history:
        return None

    # 把 history 里的用例名映射成中文标题，方便图表展示
    titles = CASE_TITLES

    html = _trend_html(history, titles)
    TREND_HTML.write_text(html, encoding="utf-8")
    return TREND_HTML


def _trend_html(history: list, titles: dict) -> str:
    """趋势页主体：专业测试仪表盘（Chart.js 交互式）。

    模块：顶部 KPI / 通过率趋势 / 耗时趋势 / 失败热点 / 用例稳定率矩阵 /
          最慢用例 TOP / 失败原因聚合 / 历史明细（可搜索、可点看单用例走势）。
    纯前端计算，数据由 history.json 注入。
    """
    payload = json.dumps(history, ensure_ascii=False)
    titles_json = json.dumps(titles, ensure_ascii=False)

    # Chart.js 内嵌(而非 CDN): 报告离线/内网/预览面板都能打开, 不依赖外网
    chart_js = ""
    chart_src = REPORT_DIR / "_chart.umd.min.js"
    if chart_src.exists():
        try:
            chart_js = chart_src.read_text(encoding="utf-8")
        except Exception:
            chart_js = ""
    if not chart_js:
        # 兜底: 本地文件丢了就退回 CDN
        chart_js = 'document.write(\'<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"><\\/script>\');'

    html = (_TREND_TPL.replace("__CHARTJS__", chart_js)
                    .replace("__PAYLOAD__", payload)
                    .replace("__TITLES__", titles_json)
                    .replace("__N__", str(len(history))))
    return html


_TREND_TPL = """<!DOCTYPE html>
<html lang="zh"><head><meta charset="utf-8"><title>xLean 测试质量报告</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script>__CHARTJS__</script>
<style>
:root{
  --bg:#0d0f13; --card:#151820; --card2:#1c202b; --line:#262b36;
  --txt:#e8eaef; --sub:#9aa3b2; --dim:#626b7a;
  --ok:#22c55e; --bad:#ef4444; --warn:#f59e0b; --info:#3b82f6; --skip:#64748b;
}
*{box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;margin:0;background:var(--bg);color:var(--txt);-webkit-font-smoothing:antialiased}
.wrap{max-width:1240px;margin:0 auto;padding:26px 22px 60px}

/* 结论横幅 */
.verdict{display:flex;align-items:center;gap:18px;padding:22px 26px;border-radius:16px;border:1px solid var(--line);background:linear-gradient(135deg,var(--card),var(--card2));margin-bottom:16px;position:relative;overflow:hidden}
.verdict::before{content:'';position:absolute;inset:0;background:radial-gradient(600px 120px at 8% 0%,rgba(34,197,94,.08),transparent 60%);pointer-events:none}
.verdict.fail::before{background:radial-gradient(600px 120px at 8% 0%,rgba(239,68,68,.08),transparent 60%)}
.verdict .light{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:27px;flex:none;box-shadow:0 0 0 6px rgba(0,0,0,.2)}
.verdict .light.pass{background:rgba(34,197,94,.15);color:var(--ok);animation:pulse-ok 2.4s ease-in-out infinite}
.verdict .light.fail{background:rgba(239,68,68,.15);color:var(--bad);animation:pulse-bad 1.6s ease-in-out infinite}
@keyframes pulse-ok{0%,100%{box-shadow:0 0 0 6px rgba(0,0,0,.2),0 0 0 0 rgba(34,197,94,.35)}50%{box-shadow:0 0 0 6px rgba(0,0,0,.2),0 0 0 14px rgba(34,197,94,0)}}
@keyframes pulse-bad{0%,100%{box-shadow:0 0 0 6px rgba(0,0,0,.2),0 0 0 0 rgba(239,68,68,.4)}50%{box-shadow:0 0 0 6px rgba(0,0,0,.2),0 0 0 14px rgba(239,68,68,0)}}
.verdict h1{margin:0;font-size:20px;letter-spacing:.3px}
.verdict .vsub{margin-top:5px;color:var(--sub);font-size:13px;line-height:1.6}
.verdict .meta{margin-left:auto;text-align:right;font-size:12px;color:var(--dim);line-height:1.7;flex:none}
.verdict .meta b{color:var(--sub);font-weight:600}

/* KPI */
.kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:16px}
@media(max-width:1000px){.kpis{grid-template-columns:repeat(3,1fr)}}
@media(max-width:560px){.kpis{grid-template-columns:repeat(2,1fr)}}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:15px;position:relative;overflow:hidden;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}
.kpi:hover{transform:translateY(-3px);border-color:color-mix(in srgb,var(--ac,#3b82f6) 55%,var(--line));box-shadow:0 8px 24px rgba(0,0,0,.35)}
.kpi::after{content:'';position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--ac,#3b82f6)}
.kpi .ic{position:absolute;right:12px;top:12px;font-size:17px;opacity:.5;filter:grayscale(.15)}
.kpi .v{font-size:25px;font-weight:800;font-variant-numeric:tabular-nums;line-height:1;letter-spacing:-.5px}
.kpi .v small{font-size:13px;font-weight:600;color:var(--sub)}
.kpi .t{font-size:12px;color:var(--sub);margin-top:9px}
.kpi .d{font-size:11px;color:var(--dim);margin-top:3px}
.kpi .trend{font-size:11px;margin-top:6px;font-weight:600}
.up{color:var(--ok)} .down{color:var(--bad)} .flat{color:var(--dim)}

/* 通用卡片 */
.grid{display:grid;gap:14px;margin-bottom:14px}
.g2{grid-template-columns:1fr 1fr}
.g32{grid-template-columns:1.6fr 1fr}
@media(max-width:900px){.g2,.g32{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:18px;transition:border-color .18s ease,box-shadow .18s ease}
.card:hover{border-color:#303748;box-shadow:0 6px 22px rgba(0,0,0,.28)}
.card h2{margin:0 0 2px;font-size:14px;font-weight:700;display:flex;align-items:center;gap:8px}
.card h2 .hico{font-size:15px;opacity:.85}
.card h2 .badge{font-size:10px;font-weight:700;padding:2px 8px;border-radius:5px;background:var(--card2);border:1px solid var(--line);color:var(--sub)}
.card .meta{color:var(--dim);font-size:12px;margin-bottom:14px;line-height:1.5}
canvas{max-height:280px}

/* 缺陷清单 */
.defect{border:1px solid rgba(239,68,68,.35);border-left:3px solid var(--bad);border-radius:10px;padding:13px 15px;margin-bottom:10px;background:rgba(239,68,68,.04)}
.defect .df-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:7px}
.defect .df-name{font-weight:700;font-size:13.5px}
.defect .tag{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid}
.tag.reg{color:#fca5a5;border-color:rgba(239,68,68,.4);background:rgba(239,68,68,.12)}
.tag.flaky{color:#fbbf24;border-color:rgba(245,158,11,.4);background:rgba(245,158,11,.12)}
.tag.new{color:#93c5fd;border-color:rgba(59,130,246,.4);background:rgba(59,130,246,.12)}
.tag.slow{color:#fbbf24;border-color:rgba(245,158,11,.4);background:rgba(245,158,11,.12)}
.defect .df-desc{font-size:12.5px;color:var(--sub);line-height:1.65}
.defect .df-trace{font-size:11.5px;color:var(--dim);margin-top:6px;font-family:ui-monospace,Consolas,monospace}

/* 稳定率矩阵 */
.matrix-tbl{width:100%;border-collapse:collapse;font-size:12.5px}
.matrix-tbl th{text-align:left;color:var(--dim);font-weight:600;padding:8px 8px;border-bottom:1px solid var(--line);font-size:11px;white-space:nowrap}
.matrix-tbl td{padding:8px;border-bottom:1px solid #1b1e27;vertical-align:middle}
.matrix-tbl tr:hover td{background:#191d26}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:4px;vertical-align:middle}
.cell{display:inline-block;width:16px;height:16px;border-radius:4px;margin-right:4px;cursor:pointer;border:1px solid transparent}
.cell:hover{border-color:var(--info)}
.cell.pass{background:rgba(34,197,94,.5)} .cell.fail{background:var(--bad)} .cell.err{background:#7f1d1d} .cell.skip{background:#334155}
.mrow{cursor:pointer}
.mrow:hover td{background:#191d26!important}
.stable{color:var(--ok);font-weight:700}.warn{color:var(--warn);font-weight:700}.unstable{color:var(--bad);font-weight:700}
.flaky-tag{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:5px;background:rgba(245,158,11,.15);color:var(--warn);font-size:10px;font-weight:700}

/* 明细表 */
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:var(--dim);font-weight:600;padding:9px 10px;border-bottom:1px solid var(--line);font-size:12px;white-space:nowrap}
td{padding:10px;border-bottom:1px solid #1b1e27;vertical-align:top}
tr:hover td{background:#191d26}
.cname{display:inline-block;cursor:pointer;padding:2px 8px;border-radius:5px;margin:1px 3px 1px 0;transition:.12s;border:1px solid transparent;font-size:12.5px}
.cname:hover{background:var(--card2);border-color:var(--line)}
.cname.sel,.mrow.sel td{background:rgba(59,130,246,.12)}
.cname.sel{border-color:var(--info)}
.sec{font-size:11px;color:var(--dim)}
.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
.pill{padding:6px 13px;border-radius:999px;border:1px solid var(--line);background:var(--card);cursor:pointer;font-size:12.5px;color:var(--sub);user-select:none;transition:.15s}
.pill:hover{border-color:var(--info);color:var(--txt)}
.pill.on{background:var(--info);color:#fff;border-color:var(--info)}
.search{margin-left:auto;background:var(--card2);border:1px solid var(--line);border-radius:8px;padding:7px 12px;color:var(--txt);font-size:13px;width:210px;outline:none}
.search:focus{border-color:var(--info)}
.footer{color:var(--dim);font-size:11px;text-align:center;margin-top:26px;line-height:1.8}
.empty{color:var(--dim);text-align:center;padding:24px;font-size:13px}
</style></head><body><div class="wrap">

<div class="verdict" id="verdict"></div>
<div class="kpis" id="kpis"></div>

<div id="defects-section"></div>

<div class="grid g2">
  <div class="card"><h2><span class="hico">📈</span>通过率趋势</h2><div class="meta">每次运行通过率，虚线为历史均值基线</div><canvas id="c-rate"></canvas></div>
  <div class="card"><h2><span class="hico">⏱️</span>总耗时趋势</h2><div class="meta">每次运行累计耗时（秒），红色=有失败</div><canvas id="c-time"></canvas></div>
</div>

<div class="grid g32">
  <div class="card"><h2><span class="hico">🎯</span>用例稳定率矩阵 <span class="badge" id="flaky-count"></span></h2><div class="meta">每行一个用例，色块=历次运行结果，点任一行看下方走势；标黄=不稳定(Flaky)</div><div id="matrix"></div></div>
  <div class="card"><h2><span class="hico">🐌</span>最慢用例 TOP5</h2><div class="meta">按历史平均耗时排序，超过 SLA 阈值标红</div><canvas id="c-slow"></canvas></div>
</div>

<div class="grid g2">
  <div class="card"><h2><span class="hico">🔥</span>失败热点</h2><div class="meta">各用例累计失败次数（FAIL + ERROR）</div><canvas id="c-fail"></canvas></div>
  <div class="card"><h2><span class="hico">📉</span>单用例耗时走势</h2><div class="meta" id="case-meta">点击上方矩阵或下方明细的用例名查看</div><canvas id="c-case"></canvas></div>
</div>

<div class="card">
  <div class="toolbar">
    <h2 style="margin:0"><span class="hico">📋</span>历史运行明细</h2>
    <span class="pill on" data-f="all">全部</span>
    <span class="pill" data-f="fail">失败过的</span>
    <input class="search" id="q" placeholder="搜索用例&#8230;">
  </div>
  <table><thead><tr><th>运行#</th><th>时间</th><th>结果</th><th>通过率</th><th>耗时</th><th>用例明细</th></tr></thead><tbody id="tbl"></tbody></table>
</div>

<div class="footer">数据源 history.json · 每次跑 Appium 回归自动追加 · SLA 阈值：单用例 120s / 全量 20min · 点用例名下钻历史耗时</div>
</div>

<script>
const H = __PAYLOAD__;
const TITLES = __TITLES__;
const title = n => TITLES[n] || n;
const C = {ok:'#22c55e',bad:'#ef4444',warn:'#f59e0b',info:'#3b82f6',skip:'#64748b'};
const SLA_CASE = 120;   // 单用例 SLA 秒
const SLA_TOTAL = 1200; // 全量 SLA 秒（20min）

let caseFilter='all', selectedCase=null, searchText='';
let charts={};
function destroy(n){ if(charts[n]){charts[n].destroy(); delete charts[n];} }
function cnv(id){ return document.getElementById(id); }
const lbl = r => r.ts.slice(5,16);
const stColor = s => ({PASS:C.ok,FAIL:C.bad,ERROR:C.bad,SKIP:C.skip}[s]||C.skip);
const isFail = s => ['FAIL','ERROR'].includes(s);
const uniq = () => [...new Set(H.flatMap(r=>r.cases.map(c=>c.name)))];
const caseByName = (r,n) => r.cases.find(c=>c.name===n);

/* 判断 Flaky：存在 pass 之后又 fail（或 fail 之后又 pass）的用例 */
function isFlaky(name){
  const seq = H.map(r=>{const c=caseByName(r,name);return c? (isFail(c.status)?'F':'P') : null;}).filter(Boolean);
  if(seq.length<2) return false;
  return seq.some((s,i)=> i>0 && s!==seq[i-1]);
}
/* 最近一次是否失败 */
function lastFailed(name){
  for(let i=H.length-1;i>=0;i--){const c=caseByName(H[i],name); if(c) return isFail(c.status);}
  return false;
}

/* 顶部结论 */
function verdict(){
  const last = H[H.length-1];
  const total = H.reduce((a,r)=>a+r.total,0);
  const passed = H.reduce((a,r)=>a+r.passed,0);
  const rate = total? passed/total : 0;
  const ok = last.failed===0;
  const el = cnv('verdict');
  const light = ok? 'pass':'fail';
  const ico = ok? '✔':'✖';
  let msg;
  if(ok) msg = '本轮回归 <b>全部 '+last.passed+' 条用例通过</b>，质量可发布。';
  else msg = '本轮 <b>'+last.failed+' 条用例失败</b>，需定位并修复后复测。';
  const reg = lastFailedAnyNewRegression();
  el.innerHTML =
    '<div class="light '+light+'">'+ico+'</div>'+
    '<div><h1>'+ (ok?'PASS · 回归通过':'FAIL · 回归失败') +'</h1>'+
    '<div class="vsub">'+msg+(reg? ' <span style="color:var(--bad)">其中 <b>'+reg+'</b> 条为回归(此前通过、本次失败)。</span>':'')+'</div></div>'+
    '<div class="meta">运行 #'+H.length+'<br><b>'+last.ts+'</b><br>累计通过率 <b>'+(rate*100).toFixed(1)+'%</b>（'+passed+'/'+total+'）</div>';
}
/* 统计"上次通过、本次失败"的回归数 */
function lastFailedAnyNewRegression(){
  if(H.length<2) return 0;
  const prev=H[H.length-2], last=H[H.length-1];
  let n=0;
  last.cases.forEach(c=>{
    if(!isFail(c.status)) return;
    const pc = caseByName(prev,c.name);
    if(pc && pc.status==='PASS') n++;
  });
  return n;
}

/* KPI */
function kpis(){
  const last = H[H.length-1];
  const total = H.reduce((a,r)=>a+r.total,0);
  const passed = H.reduce((a,r)=>a+r.passed,0);
  const rate = total? passed/total : 0;
  // 首次通过率 FPR：历史所有用例中，第一次运行即 PASS 的比例
  const names = uniq();
  const fpr = names.filter(n=>{const first=H[0].cases.find(c=>c.name===n); return first&&first.status==='PASS';}).length / (names.length||1);
  const avgTime = H.reduce((a,r)=>a+r.elapsed,0)/H.length;
  const best = H.reduce((a,r)=>Math.min(a,r.elapsed),1e9);
  const worst = H.reduce((a,r)=>Math.max(a,r.elapsed),0);
  const flakyNames = names.filter(isFlaky);
  const prevRate = H.length>=2? (H[H.length-2].total? H[H.length-2].passed/H[H.length-2].total:0) : rate;
  const rateDelta = H.length>=2? rate-prevRate : 0;
  const prevTime = H.length>=2? H[H.length-2].elapsed : avgTime;
  const timeDelta = H.length>=2? last.elapsed-prevTime : 0;

  const k = (v,small,t,d,ac,trendHtml,ic)=>
    '<div class="kpi" style="--ac:'+ac+'">'+(ic?'<span class="ic">'+ic+'</span>':'')+'<div class="v">'+v+(small?'<small> '+small+'</small>':'')+'</div><div class="t">'+t+'</div><div class="d">'+d+'</div>'+(trendHtml||'')+'</div>';
  const trend = (delta, goodWhenDown) => {
    if(delta===0) return '<div class="trend flat">— 持平</div>';
    const good = goodWhenDown? delta<0 : delta>0;
    const cls = good?'up':'down';
    const arrow = delta>0?'▲':'▼';
    return '<div class="trend '+cls+'">'+arrow+' '+Math.abs(delta).toFixed(1)+' '+ (goodWhenDown?'':'%') +'</div>';
  };
  cnv('kpis').innerHTML =
    k(H.length,'','运行次数','累计 '+H.length+' 次回归',C.info,'','🔄')+
    k(last.passed,'/'+last.total,'最近一次结果',last.ts.slice(0,16), last.failed? C.bad:C.ok,'', last.failed?'⚠️':'✅')+
    k((rate*100).toFixed(1),'%','累计通过率',passed+' / '+total, C.ok, trend(rateDelta*100,false),'📊')+
    k((fpr*100).toFixed(0),'%','首次通过率',names.length+' 用例首次即过', C.info,'','🚀')+
    k(flakyNames.length,'','不稳定用例',flakyNames.length? '需关注：'+flakyNames.slice(0,2).map(title).join('、')+(flakyNames.length>2?'…':''):'全部稳定', flakyNames.length?C.warn:C.ok,'', flakyNames.length?'🌀':'🛡️')+
    k(_fmt(last.elapsed),'','本次耗时', '最快 '+_fmt(best)+' / 最慢 '+_fmt(worst), last.elapsed>SLA_TOTAL?C.bad:C.info, trend(timeDelta,true),'⏱️');
}
function _fmt(s){ s=Math.round(s); if(s<60)return s+'s'; return Math.floor(s/60)+'m'+(s%60)+'s'; }

/* 缺陷清单 */
function defects(){
  const names = uniq();
  const defs = names.filter(lastFailed).map(n=>{
    const runs = H.map(r=>caseByName(r,n));
    const failCount = runs.filter(c=>c&&isFail(c.status)).length;
    const lastStatus = runs.filter(Boolean).slice(-1)[0].status;
    const flaky = isFlaky(n);
    const reg = H.length>=2 && caseByName(H[H.length-2],n) && caseByName(H[H.length-2],n).status==='PASS';
    const avgT = runs.reduce((a,c)=>a+(c?c.time:0),0)/(runs.filter(Boolean).length||1);
    const slow = avgT>SLA_CASE;
    const tags=[];
    if(reg) tags.push('<span class="tag reg">回归 Regression</span>');
    if(flaky) tags.push('<span class="tag flaky">不稳定 Flaky</span>');
    else tags.push('<span class="tag new">持续失败</span>');
    if(slow) tags.push('<span class="tag slow">超时</span>');
    return {n, failCount, lastStatus, tags:tags.join(' '), avgT};
  });
  const sec = cnv('defects-section');
  if(!defs.length){ sec.innerHTML=''; return; }
  sec.innerHTML = '<div class="card" style="margin-bottom:14px"><h2><span class="hico">🐛</span>缺陷清单 <span class="badge">'+defs.length+' 个</span></h2><div class="meta">当前仍未通过、需要修复或排查的用例</div>'+
    defs.map(d=>{
      const desc = d.lastStatus==='ERROR'
        ? '执行期间抛异常（定位器失效 / 环境异常），非断言失败，需先确认环境与元素定位。'
        : '断言未通过，页面状态与预期不符。建议结合截图核对实际 UI。';
      return '<div class="defect">'+
        '<div class="df-head"><span class="df-name">'+title(d.n)+'</span>'+d.tags+'</div>'+
        '<div class="df-desc">'+desc+'</div>'+
        '<div class="df-trace">历史失败 '+d.failCount+' 次 · 平均耗时 '+Math.round(d.avgT)+'s</div>'+
        '</div>';
    }).join('')+'</div>';
}

/* 通用图表外观 */
const TIP = {backgroundColor:'rgba(21,24,32,.95)',borderColor:'#262b36',borderWidth:1,titleColor:'#e8eaef',bodyColor:'#9aa3b2',padding:10,cornerRadius:8,displayColors:false};
const GRID = {color:'rgba(38,43,54,.6)'};
const grad = (ctx,area,rgb)=>{ const g=ctx.createLinearGradient(0,area.top,0,area.bottom); g.addColorStop(0,`rgba(${rgb},.32)`); g.addColorStop(1,`rgba(${rgb},.02)`); return g; };

/* 通过率趋势（带基线） */
function drawRate(){
  destroy('rate');
  const labels = H.map(r=>lbl(r));
  const data = H.map(r=>r.total? +(r.passed/r.total*100).toFixed(1):0);
  const avg = data.reduce((a,b)=>a+b,0)/data.length;
  charts.rate = new Chart(cnv('c-rate'), {
    type:'line',
    data:{labels,
      datasets:[
        {label:'通过率 %',data,borderColor:C.info,borderWidth:2.5,backgroundColor:c=>{const {ctx,chartArea}=c.chart; return chartArea?grad(ctx,chartArea,'59,130,246'):'rgba(59,130,246,.15)';},fill:true,tension:.35,pointRadius:4,pointHoverRadius:7,pointBackgroundColor:H.map(r=>r.failed?C.bad:C.ok),pointBorderColor:'#0d0f13',pointBorderWidth:2},
        {label:'基线均值',data:H.map(()=>+avg.toFixed(1)),borderColor:'#64748b',borderDash:[6,5],borderWidth:1.5,pointRadius:0,fill:false}
      ]},
    options:{plugins:{legend:{display:true,labels:{color:'#9aa3b2',boxWidth:12,boxHeight:12,font:{size:11}}},tooltip:TIP},scales:{x:{ticks:{color:'#626b7a'},grid:{display:false}},y:{min:0,max:100,ticks:{color:'#626b7a',callback:v=>v+'%'},grid:GRID}}}
  });
}

/* 总耗时趋势 */
function drawTime(){
  destroy('time');
  charts.time = new Chart(cnv('c-time'), {
    type:'bar',
    data:{labels:H.map(r=>lbl(r)),
      datasets:[{label:'总耗时(s)',data:H.map(r=>r.elapsed),backgroundColor:H.map(r=>r.elapsed>SLA_TOTAL?C.bad:(r.failed?C.warn:C.info)),borderRadius:4}]},
    options:{plugins:{legend:{display:false},tooltip:TIP},scales:{x:{ticks:{color:'#626b7a'}},y:{ticks:{color:'#626b7a'},grid:GRID}}}
  });
}

/* 失败热点 */
function drawFail(){
  const names=uniq();
  const fails=names.map(n=>H.reduce((a,r)=>a+(caseByName(r,n)&&isFail(caseByName(r,n).status)?1:0),0));
  destroy('fail');
  charts.fail = new Chart(cnv('c-fail'), {
    type:'bar',
    data:{labels:names.map(title),datasets:[{label:'累计失败',data:fails,backgroundColor:fails.map(f=>f>0?C.bad:'#334155'),borderRadius:3}]},
    options:{indexAxis:'y',plugins:{legend:{display:false},tooltip:TIP},scales:{x:{ticks:{color:'#626b7a'},grid:GRID},y:{ticks:{color:'#9aa3b2',font:{size:10}}}}}
  });
}

/* 最慢用例 TOP5 */
function drawSlow(){
  const names=uniq();
  const avg=names.map(n=>({n,t:H.reduce((a,r)=>{const c=caseByName(r,n);return a+(c?c.time:0);},0)/H.length})).sort((a,b)=>b.t-a.t).slice(0,5);
  destroy('slow');
  charts.slow = new Chart(cnv('c-slow'), {
    type:'bar',
    data:{labels:avg.map(x=>title(x.n)),datasets:[{label:'平均耗时(s)',data:avg.map(x=>+x.t.toFixed(1)),backgroundColor:avg.map(x=>x.t>SLA_CASE?C.bad:C.warn),borderRadius:4}]},
    options:{plugins:{legend:{display:false},tooltip:TIP},scales:{x:{ticks:{color:'#626b7a'}},y:{ticks:{color:'#626b7a'},grid:GRID}}}
  });
}

/* 单用例走势 */
function drawCase(){
  if(!selectedCase){ cnv('c-case').style.display='none'; cnv('case-meta').textContent='点击上方矩阵或下方明细的用例名查看'; return; }
  cnv('c-case').style.display='block';
  cnv('case-meta').innerHTML='正在查看：<b>'+title(selectedCase)+'</b>'+(isFlaky(selectedCase)?' <span class="flaky-tag">不稳定</span>':'');
  const data=H.map(r=>{const c=caseByName(r,selectedCase);return c?c.time:null;});
  const cols=H.map(r=>{const c=caseByName(r,selectedCase);return c?(isFail(c.status)?C.bad:(c.time>SLA_CASE?C.warn:C.info)):'#333';});
  destroy('case');
  charts.case = new Chart(cnv('c-case'), {
    type:'bar',
    data:{labels:H.map((r,i)=>lbl(r)),datasets:[{label:title(selectedCase)+' 耗时(s)',data,backgroundColor:cols,borderRadius:4}]},
    options:{plugins:{legend:{display:false},tooltip:TIP},scales:{x:{ticks:{color:'#626b7a'}},y:{ticks:{color:'#626b7a'},grid:GRID}}}
  });
}

/* 稳定率矩阵 */
function matrix(){
  const names=uniq();
  cnv('flaky-count').textContent = names.filter(isFlaky).length+' 个不稳定';
  const html = '<div style="overflow-x:auto"><table class="matrix-tbl" style="min-width:620px"><thead><tr><th style="width:42%">用例</th><th>稳定率</th><th>历次运行（左旧→右新）</th></tr></thead><tbody>'+
    names.map(n=>{
      const runs = H.map(r=>caseByName(r,n));
      const pass = runs.filter(c=>c&&c.status==='PASS').length;
      const valid = runs.filter(c=>c).length;
      const rate = valid? Math.round(pass/valid*100):0;
      const cells = runs.map(c=>{
        const cls = c? (c.status==='PASS'?'pass':(c.status==='ERROR'?'err':'fail')) : 'skip';
        return '<span class="cell '+cls+'" title="'+lbl(H[0])+'" onclick="selectCase(\\''+n+'\\')"></span>';
      }).join('');
      const flaky = isFlaky(n);
      const rateCol = rate===100?'<span class="stable">'+rate+'%</span>'
        : rate>=80? '<span class="warn">'+rate+'%</span>'
        : '<span class="unstable">'+rate+'%</span>';
      return '<tr class="mrow" data-name="'+n+'"><td>'+title(n)+(flaky?'<span class="flaky-tag">Flaky</span>':'')+'</td><td>'+rateCol+'</td><td>'+cells+'</td></tr>';
    }).join('')+'</tbody></table></div>';
  cnv('matrix').innerHTML=html;
  cnv('matrix').querySelectorAll('.mrow').forEach(tr=>{ tr.onclick=()=>selectCase(tr.dataset.name); });
}

/* 明细表 */
function drawTable(){
  const q = searchText.toLowerCase();
  const tb = cnv('tbl'); tb.innerHTML='';
  H.slice().reverse().forEach((r,idx)=>{
    const names = r.cases.map(c=>c.name);
    if(searchText && !names.some(n=>title(n).toLowerCase().includes(q) || n.toLowerCase().includes(q))) return;
    if(caseFilter==='fail' && r.failed===0) return;
    const runNo = H.length - idx;
    const rate = r.total? (r.passed/r.total*100).toFixed(0):0;
    const row=document.createElement('tr');
    row.innerHTML = '<td style="color:var(--dim);font-variant-numeric:tabular-nums">#'+runNo+'</td>'+
      '<td style="white-space:nowrap">'+r.ts+'</td>'+
      '<td>'+(r.failed===0
        ?'<span style="color:'+C.ok+';font-weight:700">'+r.passed+'/'+r.total+' 全过</span>'
        :'<span style="color:'+C.bad+';font-weight:700">'+r.passed+'/'+r.total+' · '+r.failed+' 失败</span>')+'</td>'+
      '<td style="font-variant-numeric:tabular-nums;color:'+(rate<100?C.warn:C.txt)+'">'+rate+'%</td>'+
      '<td style="white-space:nowrap;font-variant-numeric:tabular-nums;color:'+(r.elapsed>SLA_TOTAL?C.bad:'' )+'">'+_fmt(r.elapsed)+'</td>'+
      '<td>'+r.cases.map(c=>'<span class="cname" data-name="'+c.name+'"><span class="dot" style="background:'+stColor(c.status)+'"></span>'+title(c.name)+' <span class="sec">'+Math.round(c.time)+'s</span></span>').join('')+'</td>';
    tb.appendChild(row);
  });
}

function selectCase(name){
  selectedCase = name;
  document.querySelectorAll('.cname,.mrow').forEach(x=>x.classList.remove('sel'));
  document.querySelectorAll('[data-name="'+name+'"]').forEach(x=>x.classList.add('sel'));
  cnv('c-case').scrollIntoView({behavior:'smooth',block:'center'});
  drawCase();
}

document.querySelectorAll('.pill').forEach(p=>p.onclick=()=>{
  caseFilter=p.dataset.f;
  document.querySelectorAll('.pill').forEach(x=>x.classList.toggle('on',x===p));
  drawRate();drawTime();drawTable();
});
cnv('q').addEventListener('input',e=>{searchText=e.target.value;drawTable();});
cnv('tbl').addEventListener('click',e=>{const c=e.target.closest('.cname'); if(c) selectCase(c.dataset.name);});

verdict(); kpis(); defects(); matrix(); drawRate(); drawTime(); drawFail(); drawSlow(); drawCase(); drawTable();
</script></body></html>"""


async def main() -> None:
    parser = argparse.ArgumentParser(description="Appium 回归 + Artemis 探索 全流程")
    parser.add_argument("--skip-appium", action="store_true", help="跳过 Appium 回归")
    parser.add_argument("--skip-artemis", action="store_true", help="跳过 Artemis 探索")
    parser.add_argument("--report-only", action="store_true",
                        help="不跑任何测试，用上次留档数据重新生成报告")
    args = parser.parse_args()

    if args.report_only:
        # 从留档恢复（junitxml 常驻，artemis 用快照）
        cases = parse_junit(JUNIT_XML)
        tasks = load_artemis_tasks()
        ap, ap_ok = sum(1 for c in cases if c["status"] == "PASS"), len(cases)
        ar, ar_ok = sum(1 for t in tasks if t.get("ok")), len(tasks)
        appium = {"status": "PASS" if ap == ap_ok and ap_ok else ("FAIL" if ap_ok or cases else "SKIP"),
                  "detail": "（--report-only：来自上次 junitxml 留档）", "cases": cases}
        artemis = {"status": "PASS" if ar == ar_ok and ar_ok else ("FAIL" if ar_ok or tasks else "SKIP"),
                   "detail": "（--report-only：来自上次快照）", "tasks": tasks}
    else:
        appium = {"status": "SKIP", "detail": "已跳过", "cases": []}
        artemis = {"status": "SKIP", "detail": "已跳过", "tasks": []}

        if not args.skip_appium:
            appium = run_appium_regression()
            print(f"\n[Appium] {appium['status']}\n")
            if appium.get("ran_this_time") and appium.get("cases"):
                record_history(appium["cases"])
        elif JUNIT_XML.exists():
            appium = {"status": "SKIP", "detail": "已跳过（显示上次数据）",
                      "cases": parse_junit(JUNIT_XML)}

        if not args.skip_artemis:
            artemis = run_artemis_explore()
            print(f"\n[Artemis] {artemis['status']}\n")
        elif ARTEMIS_SNAPSHOT.exists():
            tasks = load_artemis_tasks()
            artemis = {"status": "SKIP", "detail": "已跳过（显示上次数据）", "tasks": tasks}

    report = write_summary(appium, artemis)
    trend = write_trend()
    print("=" * 60)
    print(f"全流程完成，报告：{report}")
    if trend:
        print(f"趋势面板：{trend}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
