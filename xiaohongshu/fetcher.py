"""小红书搜索爬虫 — 本地 HTML 解析 + 线上 Playwright 搜索。"""
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup


def _parse_item(item, scrape_time: str) -> dict | None:
    """从 section.note-item 提取单条数据。"""
    # 标题
    title_el = item.select_one("a.title")
    title = title_el.get_text(strip=True) if title_el else ""
    if not title:
        return None

    # 博主
    name_el = item.select_one(".name")
    author = name_el.get_text(strip=True) if name_el else ""

    # 发布时间
    time_el = item.select_one(".time")
    pub_time = time_el.get_text(strip=True) if time_el else ""

    # 点赞
    count_el = item.select_one(".count")
    likes = count_el.get_text(strip=True) if count_el else ""

    # 封面图
    cover_el = item.select_one("a.cover img") or item.select_one("[class*=cover] img")
    cover = ""
    if cover_el:
        cover = cover_el.get("src") or cover_el.get("data-src") or ""
        if cover.startswith("//"):
            cover = f"https:{cover}"

    # 帖子链接: /explore/{id} + xsec_token from cover href
    explore_a = item.select_one("a:not([class])")
    base_link = explore_a.get("href", "") if explore_a else ""

    # 从 a.cover 的 href 中提取 xsec_token
    cover_a = item.select_one("a.cover")
    xsec_token = ""
    if cover_a:
        parsed = urllib.parse.urlparse(cover_a.get("href", ""))
        params = urllib.parse.parse_qs(parsed.query)
        xsec_token = params.get("xsec_token", [""])[0]

    # 补全相对协议链接
    if base_link.startswith("//"):
        base_link = f"https:{base_link}"
    elif base_link.startswith("/"):
        base_link = f"https://www.xiaohongshu.com{base_link}"

    # 拼接完整链接
    link = base_link
    if xsec_token:
        sep = "&" if "?" in base_link else "?"
        link = f"{base_link}{sep}xsec_token={xsec_token}&xsec_source=pc_search&source=web_explore_feed"

    return {
        "title": title,
        "author": author,
        "pub_time": pub_time,
        "likes": likes,
        "link": link,
        "cover": cover,
        "scrape_time": scrape_time,
    }


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取搜索结果。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = soup.select("section.note-item")
    results = []

    for item in items:
        data = _parse_item(item, scrape_time)
        if data:
            results.append(data)

    if limit:
        results = results[:limit]
    return results


def from_search(keyword: str, scroll: int = 5) -> list[dict]:
    """通过 Playwright 在线搜索小红书关键词。"""
    from playwright.sync_api import sync_playwright
    from common.stealth import apply_stealth
    from xiaohongshu.auth import load_cookies, has_cookies

    url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        # 注入登录态 Cookie（必须带 domain + path）
        if has_cookies():
            formatted = []
            for k, v in load_cookies().items():
                formatted.append({
                    "name": k, "value": v,
                    "domain": ".xiaohongshu.com",
                    "path": "/",
                })
            context.add_cookies(formatted)
        page = context.new_page()
        apply_stealth(page)
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)  # 给 JS 渲染时间

        try:
            page.wait_for_selector("section.note-item", timeout=15000)
        except Exception:
            print("未找到搜索结果，可能需要登录或页面结构已变化")
            browser.close()
            return []

        for _ in range(scroll):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "lxml")
    items = soup.select("section.note-item")
    results = []

    for item in items:
        data = _parse_item(item, scrape_time)
        if data:
            results.append(data)

    return results
