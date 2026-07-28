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
        if len(p) < 4:
            continue
        if "¥" in p or "￥" in p or re.match(r"^\d+\.\d{2}$", p):
            price = p
        elif "人付款" in p or "人收货" in p:
            sales = p
        elif "天猫" in p or "淘宝" in p:
            pass
        elif len(p) > 6 and "¥" not in p and "人付款" not in p:
            if not title:
                title = p

    link = ""
    for a in item.select("a[href]"):
        href = a.get("href", "")
        if ("item.taobao.com" in href or "detail.tmall.com" in href
                or "click.simba.taobao.com" in href):
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
    # 尝试多种选择器定位商品卡片
    items = []
    for sel in [
        "div[class*=Card--doubleCard]", "[class*=Content--contentInner]",
        ".J_Item", "[class*=ItemWrap]", "div.ctx-box div[class*=item]",
        "div[class*=grid] > div > div", "div[class*=item]",
    ]:
        cards = soup.select(sel)
        if 5 <= len(cards) <= 200:
            items = cards
            break

    if not items:
        # 无匹配选择器，按价格 ¥ 反向找父元素
        seen = set()
        for el in soup.select("*"):
            t = el.get_text(strip=True)
            if "¥" in t and "人付款" in t and len(t) < 300:
                # 向上找合适容器
                parent = el.parent
                for _ in range(4):
                    parent = parent.parent
                    pid = id(parent)
                    if pid not in seen and parent.get_text(strip=True).count("¥") == 1:
                        seen.add(pid)
                        items.append(parent)
                        break

    results = []
    seen_links = set()
    for item in items:
        data = _parse_item(item, scrape_time)
        if data and data["title"] and data["link"] not in seen_links:
            seen_links.add(data["link"])
            results.append(data)

    if limit:
        results = results[:limit]
    return results
