"""小红书登录态 — Playwright 扫码登录 → Cookie 持久化。

用法:
    python -m xiaohongshu.auth           # 扫码登录，保存 Cookie
"""

import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"


def login() -> bool:
    with sync_playwright() as p:
        # 先用持久化上下文，复用已有登录态
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()

        # 直接打开登录页
        page.goto("https://www.xiaohongshu.com/login", timeout=15000)
        page.wait_for_timeout(2000)

        # 尝试找扫码标签
        try:
            qr_switch = page.locator("text=扫码登录").first
            if qr_switch.is_visible():
                qr_switch.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass

        print("请在浏览器中扫码登录小红书...")
        print("（打开小红书 App → 扫一扫 → 确认登录）")

        # 轮询检测登录状态（检查"登录"按钮是否消失）
        logged_in = False
        for _ in range(60):
            time.sleep(2)
            # 检查是否已登录: 看"登录"按钮是否消失
            login_btns = page.locator("text=登录").all()
            visible_logins = 0
            for btn in login_btns:
                try:
                    if btn.is_visible():
                        visible_logins += 1
                except Exception:
                    pass

            if visible_logins == 0:
                logged_in = True
                print("检测到登录成功！")
                break

            # 也检查 URL 是否跳转
            url = page.url
            if "login" not in url:
                logged_in = True
                print(f"页面已跳转: {url[:60]}")
                break

        if not logged_in:
            print("登录超时（2 分钟），请重试")
            browser.close()
            return False

        # 等一会儿让所有 Cookie 写入
        page.wait_for_timeout(2000)

        # 多访问几个页面，确保拿到完整 Cookie
        page.goto("https://www.xiaohongshu.com/explore", timeout=10000)
        page.wait_for_timeout(1000)

        cookies = context.cookies()
        browser.close()

        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"已保存 {len(cookies)} 个 Cookie 到 {COOKIE_FILE}")
        print("核心 Cookie:")
        for c in cookies:
            name = c.get("name", "")
            if name in ("web_session", "a1", "webId", "acw_tc"):
                print(f"  {name}: {c.get('value', '')[:30]}...")
        return True


def load_cookies() -> dict[str, str]:
    if not COOKIE_FILE.exists():
        return {}
    with open(COOKIE_FILE, encoding="utf-8") as f:
        cookies = json.load(f)
    return {c["name"]: c["value"] for c in cookies}


def has_cookies() -> bool:
    return COOKIE_FILE.exists() and len(load_cookies()) > 0


if __name__ == "__main__":
    if login():
        print("\n登录成功！测试: python -m xiaohongshu.main search --keyword 旅游")
    else:
        print("\n登录失败，请重试")
