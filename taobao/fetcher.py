"""淘宝/天猫搜索爬虫 — 本地HTML解析。

使用方法:
    1. 浏览器打开 s.taobao.com 搜索关键词，保存为 HTML
    2. python -m taobao.main file data/xxx.html --excel

注意: 淘宝需登录，且 bot 检测极强，不支持在线 Playwright 模式。
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup


def _parse_item(item, scrape_time: str) -> dict | None:
    text = item.get_text("|", strip=True)
    parts = [p.strip() for p in text.split("|") if p.strip()]

    title = ""
    price = ""
    sales = ""
    shop = ""

    for p in parts:
        if len(p) < 2:
            continue
        # 价格：含 ¥ 或纯数字价格
        if "¥" in p:
            if not price:
                m = re.search(r"¥\s*([\d,.]+)\s*(补贴后)?", p)
                price = m.group(0) if m else p[:20]
            continue
        # 销量
        if "人付款" in p:
            if not sales:
                m = re.search(r"(\d+[万+]?\+?人付款)", p)
                sales = m.group(1) if m else p[:20]
            continue
        # 店铺（省/市格式）
        if re.match(r"^[一-鿿]{2,4}[省市]$", p) and len(p) < 6:
            shop = p
            continue
        # 标题：较长文本且非价格/销量
        if len(p) > 4 and len(p) < 200 and "¥" not in p and "人付款" not in p:
            if not title:
                title = p

    # 链接
    link = ""
    for a in item.select("a[href]"):
        href = a.get("href", "")
        if ("item.taobao.com" in href or "detail.tmall.com" in href):
            link = href if href.startswith("http") else f"https:{href}"
            break

    if not title:
        return None

    return {
        "title": title, "price": price, "sales": sales,
        "shop": shop, "link": link, "scrape_time": scrape_time,
    }


def from_file(filepath: str, limit: int = None) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 淘宝卡片: div.content--CUnfXXxv（class 后缀可能变化）
    cards = soup.select("div[class*=content--]")
    cards = [c for c in cards if 100 < len(c.get_text(strip=True)) < 500]

    if not cards:
        # 备用: 按价格找父元素
        seen = set()
        for el in soup.select("*"):
            t = el.get_text(strip=True)
            if "¥" in t and "人付款" in t and len(t) < 300:
                p = el
                for _ in range(5):
                    p = p.parent
                pid = id(p)
                if pid not in seen:
                    seen.add(pid)
                    cards.append(p)

    results = []
    seen_links = set()
    for card in cards:
        data = _parse_item(card, scrape_time)
        if data and data["title"] and data["link"] not in seen_links:
            seen_links.add(data["link"])
            results.append(data)

    if limit:
        results = results[:limit]
    return results
