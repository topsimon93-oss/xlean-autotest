# -*- coding: utf-8 -*-
"""
Appium 用例编写套路 —— 照着抄就能写。

一句话核心：定位元素 → 操作它 → 断言结果，三步。全部通过 Page Object 封装，
不直接碰 driver 底层。真实范例见 testcases/android/test_xlean_app.py。

=====================================================================
第 1 步：找定位符（新手最卡这步，别手写）
=====================================================================
方法 A（推荐，可视化）：Appium Inspector，鼠标点一下元素，右侧自动给你 id/xpath。
方法 B（纯命令行，已内置）：先 dump 页面，再 grep 文字——
    adb shell uiautomator dump /sdcard/a.xml && adb pull /sdcard/a.xml
    # 在 xml 里搜你要点的按钮文字，看它的 resource-id / content-desc / text

Appium 支持 5 种定位方式（按稳定度排序）：
    1. id        = resource-id 唯一标识（最稳，优先用）
    2. aid       = accessibility id（无障碍标识，content-desc）
    3. text      = 显示文字（用户看得见，最直观）
    4. xpath     = 层级路径（兜底，别写死太深）
    5. class     = 控件类型（TextView/Button/EditText）

注意：很多 App（如 xLean）元素没有 resource-id，就用 text / content-desc 定位。
     动态文本（电量、倒计时）用正则 textMatches 匹配，见 android_xlean_page.py 的电量写法。

=====================================================================
第 2 步：写 Page Object（把界面封装成类）
=====================================================================
一个页面 = 一个类，继承 BasePage。定位符写在类属性，动作写成方法。

    from appium.webdriver.common.appiumby import AppiumBy
    from common.base_page import BasePage

    class LoginPage(BasePage):
        # —— 定位符（写上面，方便统一改）——
        _username = (AppiumBy.ID, "com.xxx:id/et_user")
        _password = (AppiumBy.ID, "com.xxx:id/et_pwd")
        _login_btn = (AppiumBy.ID, "com.xxx:id/btn_login")
        _toast = (AppiumBy.XPATH, '//*[contains(@text,"登录成功")]')

        # —— 动作（写下面，一行一个语义化步骤）——
        def login(self, user: str, pwd: str) -> "LoginPage":
            self.send_keys(self._username, user, desc="账号")
            self.send_keys(self._password, pwd, desc="密码")
            self.click(self._login_btn, desc="登录按钮")
            return self

        def login_success(self) -> bool:
            return self.wait_text("登录成功", timeout=5)

=====================================================================
第 3 步：写用例（点几下 → 断言结果）
=====================================================================
一个用例 = 一个 test_ 函数，靠 fixture 拿到 page，断言用 assert。

    import pytest
    from pages.login_page import LoginPage

    @pytest.fixture
    def login_page(driver):
        return LoginPage(driver)

    def test_login_ok(login_page):
        login_page.login("admin", "123456")
        assert login_page.login_success(), "登录成功提示未出现"

    def test_wrong_password_shows_error(login_page):
        login_page.login("admin", "wrong")
        assert login_page.wait_text("密码错误", timeout=5), "错误提示未出现"

=====================================================================
BasePage 已封装好的方法（直接用，别自己写 driver 操作）
=====================================================================
    find(locator, desc=)          找到元素（找不到抛 TimeoutError 并自动截图）
    find_all(locator)             找一组元素
    is_visible(locator, timeout=) 元素在不在（返回 bool，不抛错）
    click(locator, desc=)         点一下（desc 会写进日志，方便看）
    send_keys(locator, text, desc=) 输入文字
    get_text(locator)             读文字
    wait_visible / wait_gone      等待元素出现/消失
    wait_text(text)               等待页面上出现某段文字（断言提示语超好用）
    swipe(direction, times=)      滑动 up/down/left/right
    back()                        返回键
    screenshot(name) / dump(name) 截图 / dump 留证

定位符简写（_resolve 支持）：
    "id=xxx"  → 按 id
    "aid=xxx" → 按 accessibility id
    "xpath=..." / "name=..." / "class=..."
    或直接传 tuple：(AppiumBy.ID, "xxx")

=====================================================================
写用例的 5 条铁律
=====================================================================
1. 一个用例只测一件事，函数名 + 中文注释说清测什么。
2. 断言用 assert + 一句中文失败提示（例：assert x, "登录成功提示未出现"）。
3. 别写死数值断言动态内容（电量/时间/金额），改成"格式合法"或"存在"。
4. 先跑 --collect-only 确认用例被收集，再实跑。
5. 千万别点会干扰真实业务的按钮（暂停/停止/删除/确认支付…），
   只读优先，操作类想清楚再写。

=====================================================================
怎么跑
=====================================================================
    cd C:/Users/xlean/WorkBuddy/2026-09-02-13-57-28/AppAutoTest
    .venv\Scripts\python.exe -m pytest testcases/android/test_你的文件.py --platform android -v
    # 只跑其中一个用例：文件后面加 ::函数名
    .venv\Scripts\python.exe -m pytest testcases/android/test_你的文件.py::test_login_ok --platform android -v

写完记得把用例名加到 run_full_pipeline.py 顶部的 CASE_TITLES 字典里，
全流程报告就会显示中文名。
"""
