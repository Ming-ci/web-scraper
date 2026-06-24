"""07 — 滚动加载：模拟鼠标滚轮，触发懒加载/无限滚动。

核心概念：
    page.evaluate(js_code)                    → 在浏览器中执行 JavaScript
    window.scrollBy(0, pixels)                → 滚动页面
    page.mouse.wheel(delta_x, delta_y)        → 模拟鼠标滚轮
    locator.scroll_into_view_if_needed()      → 滚动到元素可见

适用场景：
    - 无限滚动（微博、Twitter、Pinterest）
    - 懒加载图片（滚动到才加载 src）
    - SPA 动态加载更多内容

本文演示：滚动当当搜索结果页到底部，触发分页区域加载。
"""

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 打开搜索结果页
        url = "http://search.dangdang.com/?key=Python&act=input"
        page.goto(url, timeout=15000)

        # 记录初始商品数
        initial_count = len(page.locator("ul.bigimg > li").all())
        print(f"初始可见商品: {initial_count} 个")

        # === 方法 1: JavaScript 滚动 ===
        print("\n[方法 1] 执行 JavaScript 滚动到页面底部...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)  # 给页面时间响应

        after_js = len(page.locator("ul.bigimg > li").all())
        print(f"  JS 滚动后可见: {after_js} 个")

        # === 方法 2: 鼠标滚轮 ===
        print("\n[方法 2] 模拟鼠标滚轮向下滚动...")
        for i in range(3):
            page.mouse.wheel(0, 500)  # 每次向下滚 500px
            page.wait_for_timeout(500)

        after_wheel = len(page.locator("ul.bigimg > li").all())
        print(f"  鼠标滚轮后可见: {after_wheel} 个")

        # === 方法 3: 滚动到特定元素 ===
        print("\n[方法 3] 滚动到倒数第 5 个商品...")
        items = page.locator("ul.bigimg > li").all()
        if len(items) > 5:
            items[-5].scroll_into_view_if_needed()
            page.wait_for_timeout(500)

        after_scroll_to = len(page.locator("ul.bigimg > li").all())
        print(f"  滚动到元素后可见: {after_scroll_to} 个")

        browser.close()


if __name__ == "__main__":
    run()
