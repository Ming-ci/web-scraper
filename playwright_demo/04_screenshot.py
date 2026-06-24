"""04 — 截图与调试。

核心概念：
    page.screenshot(path)              → 全页截图
    locator.screenshot(path)           → 单个元素截图
    page.set_viewport_size({w, h})     → 设置浏览器窗口大小
    page.pdf(path)                     → 导出 PDF（仅 headless 模式）

    截图是调试爬虫最有力的工具——先看看浏览器"看到了什么"。
"""

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 设置视口（模拟桌面浏览器）
        page.set_viewport_size({"width": 1280, "height": 800})

        url = "https://www.dangdang.com/"
        page.goto(url, wait_until="networkidle", timeout=15000)

        # === 全页截图 ===
        page.screenshot(path="data/dangdang_fullpage.png", full_page=False)
        print("全页截图已保存: data/dangdang_fullpage.png")

        # === 搜索框截图 ===
        search_box = page.locator("input[name='key']").first
        if search_box.is_visible():
            search_box.screenshot(path="data/dangdang_searchbox.png")
            print("搜索框截图已保存: data/dangdang_searchbox.png")

        # === 全页截图（含滚动区域） ===
        page.screenshot(path="data/dangdang_full_scroll.png", full_page=True)
        print("全页截图（含滚动）已保存: data/dangdang_full_scroll.png")

        browser.close()


if __name__ == "__main__":
    run()
