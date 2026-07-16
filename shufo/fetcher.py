"""AI佛书网 (shu.fo) 爬虫 — Playwright 动态渲染。

DOM: a[href*="/document/"] 的父容器含全部字段
"""

import re
from datetime import datetime

from bs4 import BeautifulSoup


def _parse_container(container, scrape_time: str) -> dict | None:
    """从包含 /document/ 链接的父容器解析书籍数据。"""
    text = container.get_text("|", strip=True)
    parts = [p.strip() for p in text.split("|") if p.strip()]

    # 名称：第一个长文本
    title = ""
    for p in parts:
        if len(p) > 10 and "书豆" not in p and "页" not in p and "MB" not in p and "天前" not in p:
            title = p
            break
    if not title:
        return None

    # 书豆
    beans = ""
    m = re.search(r"(\d+)\s*书豆", text)
    if m:
        beans = m.group(1)

    # 页数
    pages = ""
    m = re.search(r"(\d+)\s*页", text)
    if m:
        pages = m.group(1)

    # 大小
    size = ""
    m = re.search(r"([\d.]+\s*MB)", text)
    if m:
        size = m.group(1)

    # 时间
    pub_time = ""
    m = re.search(r"(\d+\s*[天小]时?前)", text)
    if m:
        pub_time = m.group(1)

    # 评分：text 中 "pub_time" 后面纯数字
    rating = ""
    if pub_time:
        idx = text.find(pub_time)
        tail = text[idx + len(pub_time):].strip("| ")
        m = re.match(r"\|?\s*(\d+)\s*\|?", tail)
        if m:
            rating = m.group(1)
    if not rating:
        m = re.search(r"([\d]+)\|?$", text)
        if m:
            r = m.group(1)
            if r.isdigit() and len(r) <= 2:
                rating = r

    # 链接
    link = ""
    for a in container.select("a[href*='/document/']"):
        href = a.get("href", "")
        link = f"https://shu.fo{href}" if href.startswith("/") else href
        break

    return {
        "title": title,
        "pages": pages,
        "size": size,
        "pub_time": pub_time,
        "rating": rating,
        "beans": beans,
        "link": link,
        "scrape_time": scrape_time,
    }


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    seen = set()
    results = []

    for a in soup.select("a[href*='/document/']"):
        # 找到足够大的父容器（含书豆/页数/MB）
        container = a
        for _ in range(8):
            container = container.parent
            t = container.get_text()
            if "书豆" in t and ("页" in t or "MB" in t):
                break

        link = a.get("href", "")
        if link in seen:
            continue
        seen.add(link)

        data = _parse_container(container, scrape_time)
        if data and data["title"]:
            results.append(data)

    if limit:
        results = results[:limit]
    return results


def from_search(pages: int = 5, limit: int = None) -> list[dict]:
    """在线爬取 shu.fo（Playwright + 翻页）。"""
    from playwright.sync_api import sync_playwright

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for pn in range(1, pages + 1):
            url = f"https://shu.fo/category?page={pn}"
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(4000)

            # 滚动触发懒加载
            for _ in range(3):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

            soup = BeautifulSoup(page.content(), "lxml")
            count = 0
            for a in soup.select("a[href*='/document/']"):
                link = a.get("href", "")
                if link in seen:
                    continue
                seen.add(link)

                container = a
                for _ in range(8):
                    container = container.parent
                    t = container.get_text()
                    if "书豆" in t:
                        break

                data = _parse_container(container, scrape_time)
                if data and data["title"]:
                    all_results.append(data)
                    count += 1

            print(f"  第 {pn} 页: {count} 条")

            if limit and len(all_results) >= limit:
                break

        browser.close()

    if limit:
        all_results = all_results[:limit]
    return all_results
