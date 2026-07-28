"""淘宝搜索自动化 — 连接真实 Chrome + 搜索翻页 + 保存HTML。

流程:
    1. 启动 Chrome（带远程调试端口）：
       chrome.exe --remote-debugging-port=9222
    2. 手动登录淘宝（一次）
    3. python -m taobao.search --keyword 机械键盘 --pages 5 --excel

原理: 连接到用户正在使用的真实 Chrome，无 Playwright 痕迹。
"""

import argparse, sys, time, os
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).parent.parent / "data"


def connect_chrome(headless: bool = False) -> "Page":
    """连接 Chrome DevTools Protocol。

    先启动 Chrome:
        chrome.exe --remote-debugging-port=9222
    """
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.new_page()
        return browser, page


def launch_chrome(headless: bool = False) -> "Page":
    """直接启动 Chrome（持久化 Profile）。"""
    from common.stealth import apply_stealth

    profile = Path(__file__).parent / "chrome_profile"
    profile.mkdir(parents=True, exist_ok=True)

    p = sync_playwright().start()
    context = p.chromium.launch_persistent_context(
        user_data_dir=str(profile),
        headless=headless,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled",
              "--no-sandbox"],
    )
    page = context.new_page()
    apply_stealth(page)
    return p, context, page


def search_keyword(page, keyword: str, max_pages: int, output_dir: str):
    """搜索关键词，翻页，保存每页 HTML。"""
    search_url = f"https://s.taobao.com/search?q={keyword}"
    page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    # 检查登录状态
    if "登录" in page.content()[:8000] and "商品" not in page.content()[:8000]:
        print("⚠ 需要登录！请在 Chrome 中手动登录淘宝，完成后按 Enter...")
        input()
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

    saved_files = []

    for pn in range(1, max_pages + 1):
        print(f"第 {pn} 页...", end=" ", flush=True)

        # 等待商品加载
        page.wait_for_timeout(2000)

        # 滚动到页面底部触发懒加载
        for _ in range(8):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(800)

        # 保存 HTML
        html = page.content()
        filename = f"taobao_{keyword}_p{pn}.html"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        saved_files.append(filepath)

        # 检查商品数
        soup = BeautifulSoup(html, "lxml")
        # 找包含 ¥ 的商品元素
        price_count = len(soup.find_all(string=lambda t: t and "¥" in t))
        print(f"{price_count} price-tags")

        if pn >= max_pages:
            break

        # 翻页：查找"下一页"按钮并点击
        try:
            next_btn = page.locator("text=下一页").first
            if next_btn.is_visible():
                next_btn.click()
                page.wait_for_timeout(3000)
            else:
                # 尝试 URL 翻页
                page_num = pn * 44  # 淘宝每页约 44 个商品
                page.goto(f"{search_url}&s={page_num}",
                          wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(3000)
        except Exception:
            page_num = pn * 44
            page.goto(f"{search_url}&s={page_num}",
                      wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(3000)

    return saved_files


def main():
    p = argparse.ArgumentParser(description="淘宝搜索自动化")
    p.add_argument("--keyword", default="机械键盘", help="搜索关键词")
    p.add_argument("--pages", type=int, default=3, help="翻页数")
    p.add_argument("--headless", action="store_true", help="无头模式")
    p.add_argument("--cdp", action="store_true",
                   help="连接到 chrome.exe --remote-debugging-port=9222")
    p.add_argument("--excel", action="store_true", help="导出 Excel")
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.cdp:
        print("连接 Chrome CDP (端口 9222)...")
        browser, page = connect_chrome()
        ctx = None
        p_inst = None
    else:
        print(f"启动 Chrome ({'无头' if args.headless else '可见'})...")
        if not args.headless:
            print("提示: 如果是首次使用，请先在弹出的浏览器中登录淘宝")
        p_inst, ctx, page = launch_chrome(headless=args.headless)
        browser = None

    try:
        files = search_keyword(page, args.keyword, args.pages, str(OUT_DIR))
        print(f"\n已保存 {len(files)} 个 HTML 文件")

        # 解析所有页面
        all_items = []
        for fp in files:
            from taobao.fetcher import from_file
            items = from_file(fp)
            all_items.extend(items)

        if all_items:
            from taobao.storage import to_excel, to_csv
            path = to_excel(all_items) if args.excel else to_csv(all_items)
            print(f"共 {len(all_items)} 条 → {path}")
        else:
            print("未提取到商品数据")
    finally:
        if browser: browser.close()
        if ctx: ctx.close()
        if p_inst: p_inst.stop()


if __name__ == "__main__":
    main()
