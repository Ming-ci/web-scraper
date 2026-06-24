"""02 — CSS 选择器与元素提取。

核心概念：
    page.locator(selector)         → 定位单个元素（懒加载）
    page.locator(selector).all()   → 定位所有匹配元素
    locator.text_content()         → 提取文本
    locator.get_attribute("href")  → 提取属性
    element.inner_text()           → 可见文本（不含隐藏元素）
"""

from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.dangdang.com/", timeout=15000)
        page.wait_for_load_state("networkidle")

        # === CSS 选择器 ===
        # 所有链接
        links = page.locator("a").all()
        print(f"全部链接: {len(links)} 个")

        # 提取前 10 个有文本的链接
        print("\n前 10 个有效链接:")
        count = 0
        for link in links:
            text = link.text_content().strip()
            href = link.get_attribute("href")
            if text and href:
                print(f"  {text[:50]} → {href[:60]}")
                count += 1
                if count >= 10:
                    break

        # === 文本匹配 ===
        # 查找包含 "图书" 文字的元素
        book_elements = page.locator("a:has-text('图书')").all()
        print(f"\n含'图书'的链接: {len(book_elements)} 个")

        # === 提取图片 ===
        imgs = page.locator("img").all()
        img_with_src = [img for img in imgs if img.get_attribute("src")]
        print(f"含 src 的图片: {len(img_with_src)} 个")
        for img in img_with_src[:3]:
            print(f"  src: {img.get_attribute('src')[:80]}")
            print(f"  alt: {img.get_attribute('alt')}")

        browser.close()


if __name__ == "__main__":
    run()
