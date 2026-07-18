"""X(Twitter)登录态 — Playwright Cookie 持久化。"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"


def login() -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://x.com/login", timeout=15000)
        page.wait_for_timeout(2000)

        print("请在浏览器中登录 X(Twitter)...")
        print("登录后脚本自动检测并保存 Cookie")

        # 等登录完成 — URL 跳转到首页
        for _ in range(90):
            page.wait_for_timeout(2000)
            if "login" not in page.url:
                break

        cookies = context.cookies()
        browser.close()

        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(cookies)} 个 Cookie")
        return True


def load_cookies() -> dict[str, str]:
    if not COOKIE_FILE.exists():
        return {}
    with open(COOKIE_FILE, encoding="utf-8") as f:
        return {c["name"]: c["value"] for c in json.load(f)}


def has_cookies() -> bool:
    return COOKIE_FILE.exists() and len(load_cookies()) > 0


if __name__ == "__main__":
    login()
