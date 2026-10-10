# apps 目录 —— 把待测 App 扔这里

放你的待测安装包, 框架会自动扫描本目录:

| 平台 | 支持的格式 | 说明 |
| --- | --- | --- |
| Android | `*.apk` | 直接安装到已连接设备/模拟器 |
| iOS | `*.ipa` | 需 macOS; `.ipa` 需先 `unzip` 得到 `Payload/*.app` 后传 .app 路径 |

## 最简用法

```bash
# 1. 扔 apk 进来
cp D:\下载\我的应用.apk apps/

# 2. 一键跑通用冒烟(自动安装 -> 启动 -> 首屏截图 -> UI dump -> Allure 报告)
scripts\run_tests.bat android apps\我的应用.apk
```

也可以不放进本目录, 直接用绝对/相对路径:

```bash
python -m pytest --platform android --app D:\下载\我的应用.apk
```

> iOS 注意: 模拟器请安装并启动后直接传 `.app` 路径; 真机传 `.ipa` 需配套签名证书与 udid。
