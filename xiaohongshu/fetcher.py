"""小红书搜索爬虫 — 本地 HTML 解析 + 线上 Playwright 搜索。"""
from datetime import datetime
from bs4 import BeautifulSoup


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取搜索结果。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    items = soup.select("section.note-item")
    results = []

    for item in items:
        data = {}
        # 标题
        title_el = item.select_one("a.title")
        data["title"] = title_el.get_text(strip=True) if title_el else ""

        # 博主
        name_el = item.select_one(".name")
        data["author"] = name_el.get_text(strip=True) if name_el else ""

        # 发布时间
        time_el = item.select_one(".time")
        data["pub_time"] = time_el.get_text(strip=True) if time_el else ""

        # 点赞
        count_el = item.select_one(".count")
        data["likes"] = count_el.get_text(strip=True) if count_el else ""

        # 封面图
        cover_el = item.select_one("a.cover img") or item.select_one("[class*=cover] img")
        data["cover"] = ""
        if cover_el:
            data["cover"] = cover_el.get("src") or cover_el.get("data-src") or ""
            if data["cover"].startswith("//"):
                data["cover"] = f"https:{data['cover']}"

        # 帖子链接
        link_el = item.select_one("a:not([class])")  # 第一个无 class 的 a
        data["link"] = link_el.get("href", "") if link_el else ""
        if data["link"].startswith("/explore"):
            data["link"] = f"https://www.xiaohongshu.com{data['link']}"

        data["scrape_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if data["title"]:
            results.append(data)

    if limit:
        results = results[:limit]
    return results


def from_search(keyword: str, scroll: int = 5) -> list[dict]:
    """通过 Playwright 在线搜索小红书关键词。

    Args:
        keyword: 搜索关键词
        scroll: 滚动加载次数
    """
    from playwright.sync_api import sync_playwright
    from common.stealth import apply_stealth

    url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        apply_stealth(page)
        page.goto(url, wait_until="networkidle", timeout=30000)

        # 等待搜索结果
        try:
            page.wait_for_selector("section.note-item", timeout=15000)
        except Exception:
            print("未找到搜索结果，可能需要登录或页面结构已变化")
            browser.close()
            return []

        # 滚动加载更多
        for _ in range(scroll):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "lxml")
    items = soup.select("section.note-item")
    results = []

    for item in items:
        data = {}
        title_el = item.select_one("a.title")
        data["title"] = title_el.get_text(strip=True) if title_el else ""
        name_el = item.select_one(".name")
        data["author"] = name_el.get_text(strip=True) if name_el else ""
        time_el = item.select_one(".time")
        data["pub_time"] = time_el.get_text(strip=True) if time_el else ""
        count_el = item.select_one(".count")
        data["likes"] = count_el.get_text(strip=True) if count_el else ""
        cover_el = item.select_one("a.cover img") or item.select_one("[class*=cover] img")
        data["cover"] = ""
        if cover_el:
            data["cover"] = cover_el.get("src") or cover_el.get("data-src") or ""
            if data["cover"].startswith("//"):
                data["cover"] = f"https:{data['cover']}"
        link_el = item.select_one("a:not([class])")
        data["link"] = link_el.get("href", "") if link_el else ""
        if data["link"].startswith("/explore"):
            data["link"] = f"https://www.xiaohongshu.com{data['link']}"
        data["scrape_time"] = scrape_time
        if data["title"]:
            results.append(data)

    return results
