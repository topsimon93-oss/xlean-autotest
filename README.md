# 📱 AppAutoTest — Android & iOS App 自动化测试框架

> 面向"扔一个 App 就能测"的一站式双端移动自动化测试项目。
> **Android 全流程可用(Windows 即可)；iOS 用例与框架同构，需 macOS + Xcode 执行。**

---

## ✨ 项目定位

```text
把 APK / IPA 扔进 apps/ 目录
   ↓
一键跑「通用冒烟」: 自动安装 → 启动 → 首屏渲染 → 稳定性 → 截图 + UI dump
   ↓
dump 出的页面结构 xml + 截图 交给 AI/人工
   ↓
自动生成 Page Object 与业务用例 → 回归 → Allure 可视化报告
```

以后你**只需要把 App 文件丢给我**, 告诉我测什么, 剩下的全链路由本框架自动完成。

---

## 🚀 快速开始 (Windows / Android)

```bash
# 0) 一次性环境准备(建 venv + 装依赖 + 装 Appium 驱动)
scripts\setup_env.bat
scripts\appium_install.bat      # 按提示装 Node → appium → uiautomator2

# 1) 起设备 + 起 Appium Server(各开一个窗口, 保持运行)
scripts\start_emulator.bat      # 启动模拟器; 连真机则确保 adb devices 可见
scripts\start_appium.bat

# 2) 扔 App + 一键通用冒烟
scripts\run_tests.bat android apps\你的应用.apk

# 3) 打开 Allure 报告
scripts\allure_report.bat
```

对应 Git Bash / macOS 使用 `scripts/*.sh`(用法一致)。

### 最常用的原始命令

```bash
python -m pytest --platform android --app apps/demo.apk                 # 通用冒烟(无需任何元素知识)
python -m pytest --platform android --with-demo                         # 跑 demo 示例(演示 PO 写法; 需设备有计算器或 local.yaml 指向它)
python -m pytest -m selfcheck                                          # 框架自检(纯逻辑, 不需要设备/Server, 任何平台可跑)
python -m pytest --platform ios   --app apps/Demo.app                   # iOS(macOS 上)
python -m pytest --platform android -k 登录                             # 按关键词过滤用例
```

---

## 🧩 能力矩阵

| 能力 | Android | iOS | 说明 |
| --- | :-: | :-: | --- |
| 通用冒烟(任意 App) | ✅ | ✅ | 安装/启动/首屏/稳定/截图/UI dump |
| Page Object 双端定位 | ✅ | ✅ | 一套元素定义自动按平台取用 |
| 真机 + 模拟器 | ✅ | ✅ | Android 自动探测 adb 设备 |
| Allure 报告/截图/xml 附件 | ✅ | ✅ | 失败自动截图 |
| 本机执行 | ✅ Windows | ⚠️ 仅 macOS | iOS 依赖 Xcode/XCUITest, **Windows 无法执行**, 但可开发与维护用例(会自动 skip) |
| 多设备并行 (pytest-xdist) | ✅ | ✅ | 预留 |

---

## 📁 目录结构

```text
AppAutoTest/
├── apps/                     # ← 把你的 APK/IPA 放这里
├── config/
│   ├── global.yaml           # 平台/等待/报告 全局配置
│   └── local.yaml.example    # 个人私有配置模板(复制为 local.yaml)
├── common/                   # 框架核心
│   ├── config.py             # YAML 配置中心(global+local 深合并)
│   ├── logger.py             # 滚动日志 logs/autotest.log
│   ├── driver_manager.py     # Appium 会话管理(Android/iOS)
│   ├── base_page.py          # PageObject 基类(双端定位符解析)
│   └── utils/                # allure 截图、UI dump、文件工具
├── pages/                    # 页面对象(示例: android_calculator_page.py)
├── testcases/
│   ├── conftest.py           # CLI 参数、平台隔离、driver 会话
│   ├── generic/              # ★ 通用冒烟(任意 App, 零元素依赖)
│   ├── android/              # Android 业务用例
│   └── ios/                  # iOS 业务用例(模板已内置)
├── scripts/                  # 一键脚本 (.bat + .sh)
├── docs/                     # 方案设计 / 流程图 / 接入指南 / 环境搭建
├── allure-results/           # pytest 原始结果
├── reports/dumps/            # UI 层级 xml(供 AI 分析)
├── screenshots/              # 截图存档
└── logs/                     # 运行日志
```

---

## ⚙️ 配置要点

| 配置 | 位置 | 作用 |
| --- | --- | --- |
| 平台全局参数 | `config/global.yaml` | 设备、包名、等待策略、报告目录 |
| 个人设备覆盖 | `config/local.yaml` | 私有设备/被测 App 写这里, 不提交 git |
| 命令行覆盖(最高优先) | `--platform/--app/--udid/--appium-server` | 单次运行临时指定 |

**为什么分两层?** global.yaml 是团队公共默认; local.yaml 只属于你(比如你的模拟器序列号、你的被测 App 包名), 换机器不冲突。

---

## 📐 定位符双端设计(核心)

元素在 Page Object 里用一个字典描述, **平台自动取用**:

```python
LOGIN_BTN = {
    "android": (AppiumBy.ID, "com.demo:id/login"),
    "ios":     (AppiumBy.ACCESSIBILITY_ID, "登录"),
    # "default": ...   # 可选兜底
}
page.click(LOGIN_BTN, desc="点击登录")
```

也支持简写字符串: `"id=xxx"` `"xpath=//xxx"` `"aid=登录"` `"name=xxx"` `"class=xxx"`。

---

## 📄 文档导航

| 文档 | 内容 |
| --- | --- |
| `docs/总览页面.html` | ★ 单页可视化总览（架构图 / 快速开始 / 能力矩阵 / 状态） |
| `docs/01-方案设计文档.md` | 完整方案: 架构、技术选型、设计要点、CI、风险与路线图 |
| `docs/02-流程图.md` | 全量流程图(架构 / 主流程 / App 接入 / PO 时序) |
| `docs/03-接入新APP与测试流程.md` | ★ 你扔一个 App 后, 全流程怎么跑 |
| `docs/04-环境搭建-Windows与Mac.md` | 两平台完整环境搭建 + 常见问题 |

---

## ⚠️ 重要限制说明

1. **iOS 不能在本机(Windows)执行**: XCUITest 依赖 Xcode。本项目 iOS 用例/元素模板已就绪, 可提交到 CI 或用 Mac 执行; 在 Windows 上运行会自动 skip, **不影响 Android 跑批**。
2. **通用冒烟 ≠ 业务用例**: 冒烟保证 App 能装、能开、不崩、产出首屏结构; 深水区业务逻辑(登录/下单…)需要基于 dump 结果补充用例。
3. 模拟器建议开启 **开发者选项 + USB 调试**; 被测 App 若有越权弹窗, `autoGrantPermissions` 已默认开启。

---

## 🔧 常见问题 FAQ

**Q1: 模拟器起不来 / 卡在 offline / qemu 启动约 30~40 秒后无声退出(breakpad 崩溃)**
- 这类问题几乎都是 **加速/渲染路径在本机不可用**导致的, 常见于: **嵌套虚拟化环境(云主机/虚拟机内)**、WSL2/Hyper-V 冲突、Windows 预览版。实测两个典型症状:
  - WHPX 加速 → qemu 约 35 秒 **ACCESS_VIOLATION 崩溃**(宿主为虚拟机时 WHPX vCPU 执行不稳定);
  - `-accel off`(TCG) + 默认宿主 GPU → 约 40 秒崩溃(宿主显卡/gfxstream 路径);
  - 进程虽活着但 `adb devices` 长期 offline / 全部线程 Suspended → 客体内 adbd 未启动(纯软件模拟极慢, 且后台任务可能被环境挂起)。
- 判定加速是否可用: 在 SDK 目录运行 `emulator-check.exe accel`。
- **稳定组合(纯软件渲染 + 纯软件模拟, 慢但能活)**:
  ```bat
  emulator -avd <你的AVD> -accel off -gpu guest -no-snapshot -cores 4
  ```
  启动需 15~30 分钟, 建议只在需要时启动一次并保持运行。**跑自动化测试建议直接用真机(USB 调试)**, 完全绕开模拟器加速问题。
- 另外建议用 **纯 AOSP / ATD 镜像**(不带 Google Play)创建 AVD, 比 `google_apis_playstore` 轻量且稳定:
  ```bat
  sdkmanager "system-images;android-34;default;x86_64"
  avdmanager create avd -n <名称> -k "system-images;android-34;default;x86_64" -d pixel_7
  ```

**Q2: `adb devices` 显示 offline**
- guest 内 adbd 尚未就绪 = 系统还在启动。等 `sys.boot_completed=1`:
  ```bat
  adb wait-for-device shell getprop sys.boot_completed
  ```

**Q3: 想先不碰设备/模拟器, 快速验证框架是否装对**
- 跑核心自检(纯逻辑, 无需任何设备):
  ```bat
  scripts\run_tests.bat android testcases/test_selfcheck_core.py
  ```
