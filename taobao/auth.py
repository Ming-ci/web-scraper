"""淘宝登录 — 持久化 Chrome Profile。"""

from pathlib import Path
from playwright.sync_api import sync_playwright

PROFILE_DIR = Path(__file__).parent / "chrome_profile"


def login():
    with sync_playwright() as p:
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR), headless=False,
            viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.goto("https://login.taobao.com/", timeout=15000)
        print("请扫码登录淘宝...完成后按 Enter")
        input()
        ctx.close()
        print("Profile 已保存")


if __name__ == "__main__":
    login()
