"""03 — 等待策略。

核心概念：
    page.wait_for_load_state(state)    → 等待页面加载状态
        "domcontentloaded"   → HTML 解析完成（最快）
        "load"              → 全部资源加载完成（图片/CSS/JS）
        "networkidle"       → 网络请求停止（最可靠，最慢）

    page.wait_for_selector(selector)   → 等待某个元素出现在 DOM
    page.wait_for_timeout(ms)          → 固定等待（不推荐，测试用）

    locator.wait_for(state="visible")  → 等待元素可见（不仅是 DOM 存在）

    等待 vs 固定 sleep：
        page.wait_for_selector(".item")  → 元素出现立即继续（快）
        time.sleep(3)                    → 总是等 3 秒，浪费时间
"""

import time
from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # === 三种加载状态对比 ===
        url = "https://www.dangdang.com/"

        # domcontentloaded: HTML 解析完就继续
        start = time.time()
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        dom_time = time.time() - start
        print(f"domcontentloaded: {dom_time:.2f}s")

        # load: 所有资源加载完
        start = time.time()
        page.goto(url, wait_until="load", timeout=15000)
        load_time = time.time() - start
        print(f"load:            {load_time:.2f}s")

        # networkidle: 网络安静后
        start = time.time()
        page.goto(url, wait_until="networkidle", timeout=15000)
        idle_time = time.time() - start
        print(f"networkidle:     {idle_time:.2f}s")

        # === 等待特定元素 ===
        print("\n等待搜索框出现...")
        page.wait_for_selector("input[name='key']", timeout=5000)
        print("  搜索框已出现！")

        # === 等待元素可见（不同于 DOM 存在） ===
        # 检查搜索框是否可见
        search_box = page.locator("input[name='key']").first
        if search_box.is_visible():
            print("  搜索框可见")
        else:
            print("  搜索框在 DOM 中但不可见")

        browser.close()


if __name__ == "__main__":
    run()
