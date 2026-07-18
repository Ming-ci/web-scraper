"""X(Twitter)登录态 — 持久化 Chrome Profile，绕过 bot 检测。"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"
PROFILE_DIR = Path(__file__).parent / "chrome_profile"


def login() -> bool:
    with sync_playwright() as p:
        # 持久化浏览器上下文（与正常 Chrome 行为完全一致）
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
        )
        page = context.new_page()
        page.goto("https://x.com/login", timeout=15000)

        print("请在浏览器中登录 X(Twitter)（邮箱 → 密码 → 验证码）")
        print("登录完成后回到这里按 Enter...")
        input()

        cookies = context.cookies()
        context.close()

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
    return "auth_token" in load_cookies()


if __name__ == "__main__":
    login()
