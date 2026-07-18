"""X(Twitter)登录态 — Playwright 手动登录。"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"


def login() -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        from common.stealth import apply_stealth
        apply_stealth(page)
        page.goto("https://x.com/login", timeout=15000)

        print("请在浏览器中登录 X(Twitter)（邮箱 → 密码 → 验证码）")
        print("登录完成后回到这里按 Enter...")
        input()

        cookies = context.cookies()
        browser.close()

        names = {c["name"] for c in cookies}
        if "auth_token" not in names:
            print(f"缺少 auth_token，登录未完成。已有 Cookie: {names}")
            return False

        simple = [{"name": c["name"], "value": c["value"]} for c in cookies]
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(simple, f, ensure_ascii=False, indent=2)
        print(f"已保存 {len(cookies)} 个 Cookie (含 auth_token)")
        return True


def load_cookies() -> dict[str, str]:
    if not COOKIE_FILE.exists():
        return {}
    with open(COOKIE_FILE, encoding="utf-8") as f:
        return {c["name"]: c["value"] for c in json.load(f)}


def has_cookies() -> bool:
    if not COOKIE_FILE.exists():
        return False
    cookies = load_cookies()
    return "auth_token" in cookies


if __name__ == "__main__":
    login()
