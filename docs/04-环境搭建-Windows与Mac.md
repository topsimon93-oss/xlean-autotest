# 04 · 环境搭建手册（Windows 与 macOS）

> 目标：把「Python + Appium 2 + 驱动 + 设备」一次性装好，让项目一条命令可跑。
> 本机已自动探测的默认路径（Windows）：Android SDK 位于
> `C:\Users\<你>\AppData\Local\Android\Sdk`，Java 可直接复用 Android Studio 自带
> JBR（`C:\Program Files\Android\Android Studio\jbr`），无需单独装 JDK。

---

## 1. Windows（Android 全流程）

### 1.0 前置软件
| 软件 | 检测命令 | 安装 |
| --- | --- | --- |
| Python 3.9+ | `python --version` | `winget install Python.Python.3.12`（勾选 Add to PATH） |
| Node.js 18+ | `node -v` | `winget install OpenJS.NodeJS.LTS` |
| Android SDK | `adb version` | Android Studio → SDK Manager（装 platform-tools / emulator / 一个 system-image） |
| Java（可选） | `java -version` | **免装**：SDK 脚本会自动用 Android Studio 自带 JBR |

### 1.1 一键初始化（项目根目录执行）

```bat
:: 第 1 步: Python 依赖(建 .venv + pip install -r requirements.txt)
scripts\setup_env.bat

:: 第 2 步: Appium 2 + uiautomator2 驱动(需要网络, 一次性)
scripts\appium_install.bat

:: 验证
appium --version
appium driver list --installed      :: 应看到 uiautomator2
adb devices                          :: 应有设备
```

### 1.2 创建模拟器（无现成 AVD 时）

```bat
:: 列出系统镜像, 任选一个
sdkmanager --list | findstr "system-images;android-3"

:: 装一个 Google APIs 镜像(以 android-34 为例)
sdkmanager "system-images;android-34;google_apis;x86_64"

:: 创建 AVD
avdmanager create avd -n test_phone -k "system-images;android-34;google_apis;x86_64" -d pixel_7

:: 启动
emulator -avd test_phone
```

> 提示：Android 模拟器与 WSL2/Hyper-V 存在虚拟化冲突的可能，若模拟器起不来，
> 常见处理顺序：① 用 `emulator -accel-check` 看加速状态；
> ② 若提示 WHPX 不可用，可改用真机（USB 调试）最省事；
> ③ 关闭 WSL2 侧 Hyper-V 或改用 `-no-accel`（很慢，仅应急）。

### 1.3 启动 Server + 跑测试

```bat
scripts\start_appium.bat            :: 保持前台运行(Ctrl+C 停止)
:: 另开一个窗口:
scripts\run_tests.bat android apps\你的App.apk
scripts\allure_report.bat           :: 生成并打开报告
```

---

## 2. macOS（iOS 全流程 / Android 同流程）

### 2.0 前置软件
- Xcode（≥ 最新稳定版）→ `xcode-select --install`
- Xcode → Settings → Components 装一个 iOS Simulator runtime
- Homebrew：`brew install node python`（或各自官方包）

### 2.1 iOS 依赖（只做一次）

```bash
# Appium XCUITest driver(替代 appium_install.bat 里的 uiautomator2)
npm install -g appium
appium driver install xcuitest

# 每次 Xcode 升级后需重建 WDA, 可交给 Appium 自动编译
```

### 2.2 启动 iOS 模拟器并验证

```bash
open -a Simulator
xcrun simctl list devices          # 拿到 udid
xcrun simctl boot "<你的模拟器名>"   # 已由 Simulator 打开则无需

# 安装被测 App 到模拟器
xcrun simctl install booted /path/to/Payload/xxx.app

scripts/setup_env.sh
scripts/start_appium.sh
scripts/run_tests.sh ios apps/xxx.app
```

> iOS 真机需：开发者证书签名 + `ios.udid` 填设备 UUID（`config/local.yaml`）。
> WebDriverAgent 首次会往真机装 WDA 并要信任开发者证书。

---

## 3. 常见环境问题速查

| 症状 | 原因/处理 |
| --- | --- |
| `python 不是内部或外部命令` | 重装 Python 勾选 Add to PATH；或用 `py -3` |
| `appium 不是内部或外部命令` | Node 的全局 bin 不在 PATH；重开终端；或 `npx appium` |
| `appium driver install` 慢/失败 | 换源：`npm config set registry https://registry.npmmirror.com` 后重试 |
| 会话报 `Could not load ... driver` | driver 没装：`appium driver install uiautomator2`（android） |
| 会话报 unknown capability `appium:xxx` | 升级 Appium：`npm install -g appium@latest` |
| `adb devices` 空 | 模拟器没起 / 真机没开 USB 调试；`adb kill-server && adb start-server` |
| `ANDROID_HOME` 报错 | 本框架默认不依赖它(自动探测 SDK 路径), 若自定义 SDK 再手动设环境变量 |
| allure 报告打不开 | 需 Java：脚本会自动指向 Android Studio JBR；或 `winget install qameta.allure` |
| WDA 编译失败(macOS/iOS) | Xcode 版本与 Appium 兼容性 → 升级 Appium + `appium driver update xcuitest` |

---

## 4. 环境变量建议（可选，写入用户级）

```powershell
# Windows PowerShell(管理员/当前用户皆可), 按需执行:
[Environment]::SetEnvironmentVariable("ANDROID_HOME",
  "$env:LOCALAPPDATA\Android\Sdk", "User")
[Environment]::SetEnvironmentVariable("JAVA_HOME",
  "C:\Program Files\Android\Android Studio\jbr", "User")
```

```bash
# macOS ~/.zshrc
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator
```

> 框架脚本内置了"探测兜底"（找不到 ANDROID_HOME 时自动找常见安装位置，
> 找不到 JAVA_HOME 时自动用 Android Studio JBR），所以不设环境变量也能跑。
