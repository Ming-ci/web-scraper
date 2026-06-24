"""01 — 浏览器启动、页面导航、获取基础信息。

核心概念：
    sync_playwright()  →  Playwright 入口
    browser.launch(headless=True/False)  → 启动浏览器（True=无头, False=可见窗口）
    browser.new_page()  →  新建标签页
    page.goto(url)  →  导航到 URL
    page.title()  →  获取页面标题
"""

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        # 启动 Chromium（无头模式——不显示窗口）
        print("启动浏览器...")
        browser = p.chromium.launch(headless=True)

        # 新建页面
        page = browser.new_page()

        # 导航
        print("加载页面...")
        page.goto("https://www.dangdang.com/", timeout=15000)

        # 获取页面信息
        print(f"  标题: {page.title()}")
        print(f"  当前 URL: {page.url}")
        print(f"  页面内容长度: {len(page.content())} 字符")

        # 关闭浏览器
        browser.close()
        print("浏览器已关闭。")


if __name__ == "__main__":
    run()
