"""06 — 输入文本、点击按钮、等待结果。

核心概念：
    locator.fill(text)           → 清空输入框 + 输入文本（比 type() 更快）
    locator.click()              → 鼠标点击元素
    page.wait_for_selector()     → 等待操作后的结果出现
    page.wait_for_url(pattern)   → 等待 URL 跳转到匹配模式

模仿用户行为：
    1. 打开当当首页
    2. 在搜索框输入 "Python"
    3. 点击搜索按钮
    4. 等待搜索结果页面加载
    5. 提取结果
"""

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 1. 打开首页
        print("1. 打开当当首页...")
        page.goto("https://www.dangdang.com/", timeout=15000)
        page.wait_for_load_state("networkidle")

        # 2. 定位搜索框并输入
        print("2. 输入关键词 'Python'...")
        search_input = page.locator("input[name='key']").first
        search_input.wait_for(state="visible", timeout=5000)
        search_input.fill("Python")  # fill = 清空 + 输入

        # 3. 点击搜索按钮
        print("3. 点击搜索按钮...")
        search_btn = page.locator("input[type='submit'], button[type='submit']").first
        # 如果在页面上找不到 submit 按钮，按回车触发搜索
        if search_btn.is_visible():
            search_btn.click()
        else:
            search_input.press("Enter")

        # 4. 等待搜索结果加载
        print("4. 等待搜索结果...")
        page.wait_for_url("**/search.dangdang.com**", timeout=10000)

        # 5. 提取第一个商品
        print("5. 提取结果:\n")
        first_item = page.locator("ul.bigimg > li").first
        title = first_item.locator("p.name > a").get_attribute("title") or first_item.locator("p.name").inner_text()
        price = first_item.locator(".search_now_price").inner_text()

        print(f"  书名: {title[:80] if title else 'N/A'}")
        print(f"  价格: {price.replace(chr(0xa5), 'RMB')}")

        browser.close()


if __name__ == "__main__":
    run()
