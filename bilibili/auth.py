"""B站登录态 — Playwright 扫码登录 → Cookie 持久化。

流程:
    1. python -m bilibili.auth          # 打开浏览器，扫码登录
    2. Cookie 自动保存到 bilibili/cookies.json
    3. 后续 API 请求自动加载 Cookie，绕过风控

关键 Cookie（curl_cffi 格式）:
    SESSDATA, bili_jct, DedeUserID, sid
"""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

COOKIE_FILE = Path(__file__).parent / "cookies.json"


def login() -> bool:
    """打开浏览器，等待用户扫码登录 B站，保存 Cookie。

    Returns:
        True 表示登录成功并保存
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 必须可见窗口
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://passport.bilibili.com/login", timeout=15000)
        print("请在浏览器中扫码登录 B站...")
        print("（登录后脚本会自动检测并保存 Cookie）")

        # 等待登录完成 — 页面跳转到首页
        try:
            page.wait_for_url("https://www.bilibili.com/**", timeout=120000)
        except Exception:
            print("登录超时，请重试")
            browser.close()
            return False

        # 获取所有 Cookie
        cookies = context.cookies()
        browser.close()

        # 保存
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print(f"已保存 {len(cookies)} 个 Cookie 到 {COOKIE_FILE}")
        return True


def load_cookies() -> dict[str, str]:
    """从文件加载 Cookie，转为 {name: value} 字典（curl_cffi 格式）。

    Returns:
        Cookie 字典，如果文件不存在则返回空 dict
    """
    if not COOKIE_FILE.exists():
        return {}

    with open(COOKIE_FILE, encoding="utf-8") as f:
        cookies = json.load(f)

    return {c["name"]: c["value"] for c in cookies}


def has_cookies() -> bool:
    """检查是否已保存有效的 Cookie 文件。"""
    return COOKIE_FILE.exists() and len(load_cookies()) > 0


if __name__ == "__main__":
    if login():
        print("登录成功！现在可以用 python -m bilibili.up_videos --mid 17076171 30")
    else:
        print("登录失败，请重试")
