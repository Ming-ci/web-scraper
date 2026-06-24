"""05 — requests vs Playwright 实战对比。

对比目标：一个 JS 渲染的页面。
    requests → 只能拿初始 HTML，看不到 JS 生成的内容
    Playwright → 浏览器渲染完 JS 后，拿到的才是用户看到的 DOM

本例用当当网首页做对比，因为它是真实生产页面。
"""

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def run():
    url = "https://www.dangdang.com/"

    # === requests 方式 ===
    print("=" * 50)
    print("requests + BeautifulSoup")
    print("=" * 50)
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    soup = BeautifulSoup(resp.text, "lxml")

    # 统计
    a_count = len(soup.find_all("a"))
    img_count = len(soup.find_all("img"))
    script_count = len(soup.find_all("script"))
    text_len = len(resp.text)
    print(f"HTML 大小: {text_len} 字符")
    print(f"<a> 标签: {a_count}")
    print(f"<img> 标签: {img_count}")
    print(f"<script> 标签: {script_count}")

    # === Playwright 方式 ===
    print()
    print("=" * 50)
    print("Playwright (浏览器渲染后)")
    print("=" * 50)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle", timeout=15000)

        html = page.content()
        soup2 = BeautifulSoup(html, "lxml")

        a_count2 = len(soup2.find_all("a"))
        img_count2 = len(soup2.find_all("img"))
        script_count2 = len(soup2.find_all("script"))
        text_len2 = len(html)
        print(f"HTML 大小: {text_len2} 字符")
        print(f"<a> 标签: {a_count2}")
        print(f"<img> 标签: {img_count2}")
        print(f"<script> 标签: {script_count2}")

        browser.close()

    # === 差异 ===
    print()
    print("=" * 50)
    print("差异（Playwright 多拿到 JS 渲染的内容）")
    print("=" * 50)
    print(f"HTML 增量: +{text_len2 - text_len} 字符")
    print(f"<a> 增量:  +{a_count2 - a_count}")
    print(f"<img> 增量: +{img_count2 - img_count}")
    print(f"<script> 增量: +{script_count2 - script_count}")


if __name__ == "__main__":
    run()
