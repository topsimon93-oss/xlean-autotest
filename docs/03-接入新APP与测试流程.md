# 03 · 接入新 APP 与测试流程（"扔一个 App 给我" 全链路）

> 目标：**你只需要提供一个 App 安装包 + 一句话测试诉求，其余全部自动完成。**
> 本文是 AI 与框架协作的标准作业流程（SOP），每次接入新 App 都按此执行。

---

## 0. 你要做的事（只需要 3 步）

```text
① 把 APK/IPA 扔到项目 apps/ 目录（或直接丢给 AI 一个路径）
② 告诉我测什么（比如：登录、加购、下单、随便点点看崩不崩）
③ 等结果：Allure 报告 + 截图 + UI 结构 + 可复用用例
```

> 什么都不想测？只扔一个包，默认跑「通用冒烟」。

---

## 1. 全流程总览

```text
扔包
 ├─ [阶段A] 环境就绪检查（一次性的）
 │     设备在线? Appium Server 在跑? .venv 装好?
 ├─ [阶段B] 通用冒烟（对任意 App 零知识可跑）
 │     安装 → 启动 → 首屏渲染 → 短时稳定 → 截图 + UI dump(xml)
 ├─ [阶段C] AI 分析页面（关键一步）
 │     读 reports/dumps/*.xml + screenshots/*.png
 │     → 提取: 包名 / 入口 Activity / 关键元素 id·文本·层级
 ├─ [阶段D] 生成资产
 │     写 config/local.yaml（包名/入口）
 │     → 生成 pages/*.py 页面对象
 │     → 生成 testcases/** 业务用例（按你说的测试点）
 ├─ [阶段E] 回归验证 + 修正循环
 │     pytest 全量跑 → 失败看 Allure 截图定位 → 修定位符 → 再跑
 └─ [阶段F] 交付
       用例代码 + Allure 报告 + 截图/xml + 「下次直接复用」
```

---

## 2. 阶段A · 环境就绪（首次才需要）

以本机（Windows）为例，全部命令在项目根目录 `AppAutoTest/` 执行：

```bat
:: ① 初始化（建 .venv + 装 Python 依赖）
scripts\setup_env.bat

:: ② 安装 Appium 2 + uiautomator2 驱动（Node 环境，一次性）
scripts\appium_install.bat

:: ③ 启动模拟器 / 连真机（adb devices 要能看到设备）
::    然后启动 Appium Server（新窗口，保持运行）
scripts\start_appium.bat
```

自查清单：

| 检查项 | 命令 | 期望 |
| --- | --- | --- |
| Python 依赖 | `.venv\Scripts\python -m pytest --version` | pytest 8.x |
| Appium | `appium --version` | 2.x |
| 驱动 | `appium driver list --installed` | uiautomator2 ✔ |
| 设备 | `adb devices` | 至少一台 `device` |
| Server | 浏览器打开 `http://127.0.0.1:4723/status` | JSON 正常 |

> macOS 执行 iOS 时同理，见 `docs/04`。Windows 上跑 iOS 会自动 skip，不阻塞。

---

## 3. 阶段B · 通用冒烟（扔包后的第一枪）

```bat
:: 方式1：包已放进 apps/（自动取最新），一键跑
scripts\run_tests.bat android

:: 方式2：任意路径的包
scripts\run_tests.bat android apps\微信.apk

:: 方式3：等价原始命令（Git Bash 或直接终端）
.venv\Scripts\python -m pytest --platform android --app "apps\微信.apk"
```

执行后自动完成 5 项检查并产生产物：

| # | 检查 | 通过标准 | 产物 |
| --- | --- | --- | --- |
| ① | 安装并启动 | 拿到前台包名/页面 | 启动截图 |
| ② | 首屏可渲染 | page_source 非空、有节点 | page_source.xml |
| ③ | 短时稳定 | 静置后仍在（没崩） | 静置截图 |
| ④ | UI dump | xml 落盘 | `reports/dumps/*.xml` |
| ⑤ | 截图存档 | png 落盘 | `screenshots/*.png` |

> ⚠️ 冒烟**不保证业务正确**，它只回答「装得上、开得起、不崩、长啥样」。
> 深水区（登录/下单/权限流程）进入阶段 C/D。

---

## 4. 阶段C/D · AI 生成页面对象与用例（关键增值点）

AI（或人工）拿到阶段 B 的产物后按以下步骤产出，**这是本框架的核心协作契约**：

```text
输入素材
  reports/dumps/首屏_时间戳.xml   ← 页面完整层级(Android: resource-id/text/content-desc)
  screenshots/首屏_时间戳.png     ← 视觉对照
输出资产
  config/local.yaml               ← android.app_package / android.app_activity 等
  pages/<模块>/<页面>.py          ← 页面对象（一个页面一个类）
  testcases/android/test_<场景>.py ← 业务用例
```

### 4.1 读取 dump 时重点提取
- `package` 属性 → 包名；`activity` 属性 → 启动 Activity
- 每个可点击节点：`resource-id`（优先）、`text`/`content-desc`（次之）、`bounds`（坐标兜底）
- 页面模块划分：登录页 / 首页 / 列表页 / 详情页 / 我的页…

### 4.2 页面对象规范（与 demo 对齐）
- 继承 `common.base_page.BasePage`
- 定位符用「双端字典」：`{"android": (AppiumBy.ID, "..."), "ios": (AppiumBy.ACCESSIBILITY_ID, "...")}`
- 方法 = 业务动作（`login(user, pwd)`），返回 `self` 支持链式调用
- 不写死等待 sleep，统一走 `wait_visible` / `find`

### 4.3 用例规范
- 用例只描述场景、只调页面方法、只做断言
- 场景类加 marker：`android` / `ios` / 业务 marker（如 `login`）
- 关键步骤用 `allure.step` / 页面方法自带中文日志
- 需要输入中文时框架已开 `unicodeKeyboard`

---

## 5. 阶段E · 回归与修正循环

```bat
:: 全量跑当前平台（demo 默认排除）
scripts\run_tests.bat android

:: 只看某条业务线（-k 过滤）
.venv\Scripts\python -m pytest --platform android -k "登录 or 下单"

:: 失败修正循环
scripts\allure_report.bat        :: 打开报告，看失败步骤截图
:: → 通常是定位符变了 → 改 pages/ 里的元素字典 → 重跑
```

失败 90% 是三类原因，按顺序排查：

| 现象 | 处理 |
| --- | --- |
| 元素找不到（TimeoutError） | 看失败截图 → 更新定位符（优先 resource-id，其次 text，兜底 xpath/bounds） |
| App 直接崩/闪退 | 看 logcat：`adb logcat -d | findstr "FATAL AndroidRuntime"` |
| 权限弹窗拦截 | 确认 `autoGrantPermissions: true`；iOS 用 `autoAcceptAlerts` |

---

## 6. 阶段F · 交付物清单与"下次复用"

每次接入结束，项目内会沉淀：

```text
pages/        ← 页面对象资产（越积越多，换 App 版本只改定位符）
testcases/    ← 业务用例库（可重复回归）
config/local.yaml ← 该 App 的包名/入口/设备偏好
reports/dumps/    ← 每个页面的结构 xml
screenshots/      ← 视觉证据
```

**同一个 App 下次再测**：`scripts\run_tests.bat android` 一条命令全量回归。
**换新 App**：回到本文第 1 节，从阶段 B 重新走一遍即可。

---

## 7. iOS 特别说明

- 接入产物形态通常是 `xxx.ipa`；模拟器用 `unzip xxx.ipa` 解出 `Payload/xxx.app` 后传 `.app`。
- 定位策略优先级：`ACCESSIBILITY_ID`(label) → `IOS_PREDICATE` → `XPATH/CLASS_CHAIN`。
- iOS 用例同样先跑通用冒烟拿 `page_source`，再生成页面对象，流程与 Android 完全同构。
- **Windows 上无法执行 iOS 会话**（依赖 Xcode），全部自动 skip；在 Mac / CI(macOS runner) 上执行。

---

## 8. 常见问题速查

| 问题 | 解答 |
| --- | --- |
| 没传 `--app` 也没放 apps/ | 自动启动配置里的已安装包（global 默认 AOSP 计算器） |
| 多台设备 | `--udid emulator-5554` 显式指定 |
| 想连真机 | 开 USB 调试 + `adb devices` 可见即可，无需额外配置 |
| apps/ 有多个 apk | 默认取**最新**修改的那个 |
| 想跑示例用例 | 加 `demo`：`run_tests.bat android 任意.demo` |
| 中文输入不出来 | 检查 caps 里 `unicodeKeyboard/resetKeyboard=true`（默认已开） |
