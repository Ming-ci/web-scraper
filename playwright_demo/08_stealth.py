"""08 — 无头检测对比：不加 stealth vs 加 stealth。

用 https://bot.sannysoft.com 这个检测站对比效果。
"""

from playwright.sync_api import sync_playwright
from common.stealth import apply_stealth


def run():
    with sync_playwright() as p:
        # === 不加 stealth ===
        print("=" * 50)
        print("不加 stealth（原始无头浏览器）")
        print("=" * 50)

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=15000)

        # 提取检测结果
        webdriver = page.evaluate("() => navigator.webdriver")
        chrome = page.evaluate("() => !!window.chrome")
        plugins = page.evaluate("() => navigator.plugins.length")
        print(f"  navigator.webdriver: {webdriver}      ← 暴露了")
        print(f"  window.chrome:        {chrome}       ← 不存在")
        print(f"  plugins:              {plugins}              ← 0个")
        browser.close()

        # === 加 stealth ===
        print()
        print("=" * 50)
        print("加 stealth（注入反检测脚本）")
        print("=" * 50)

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        apply_stealth(page)   # ← 一行调用！必须在 goto 之前
        page.goto("https://bot.sannysoft.com/", wait_until="networkidle", timeout=15000)

        webdriver = page.evaluate("() => navigator.webdriver")
        chrome = page.evaluate("() => !!window.chrome")
        plugins = page.evaluate("() => navigator.plugins.length")
        print(f"  navigator.webdriver: {webdriver}      ← 隐藏了")
        print(f"  window.chrome:        {chrome}       ← 伪造了")
        print(f"  plugins:              {plugins}               ← 3个")

        browser.close()


if __name__ == "__main__":
    run()
