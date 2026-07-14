"""亚马逊搜索爬虫 — 本地 HTML + 在线 curl_cffi 双模式。

DOM 结构: div[data-asin]
"""

import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

CSV_COLUMNS = ["asin", "title", "price", "stars", "rating_count",
               "monthly_sales", "link", "scrape_time"]


def _parse_item(item, scrape_time: str) -> dict | None:
    """从 div[data-asin] 提取单条商品数据。"""
    asin = item.get("data-asin", "").strip()
    if not asin:
        return None

    data = {"asin": asin}
    h2 = item.select_one("h2")
    data["title"] = h2.get_text(strip=True) if h2 else ""

    # 价格
    price_whole = item.select_one(".a-price-whole")
    price_fraction = item.select_one(".a-price-fraction")
    price_symbol = item.select_one(".a-price-symbol")
    if price_whole:
        price = price_whole.get_text(strip=True)
        if price_fraction:
            price += "." + price_fraction.get_text(strip=True)
        symbol = price_symbol.get_text(strip=True) if price_symbol else ""
        data["price"] = f"{symbol} {price}" if symbol else price
        if "JPY" in data["price"]:
            parts = data["price"].split("JPY")
            if len(parts) > 1:
                data["price"] = f"JPY {parts[1].strip().split()[0]}"
    else:
        price_text = ""
        for el in item.select("span"):
            t = el.get_text(strip=True)
            if re.match(r"^(JPY|USD|EUR|GBP|¥|\$)\s*[\d,]+", t):
                price_text = t
                break
        data["price"] = price_text

    # 评分人数 "(3016)" 或 "(2.4万)"
    rating_count = ""
    for el in item.select("span"):
        text = el.get_text(strip=True)
        m = re.match(r"^\(([\d,.]+万?)\)$", text)
        if m:
            rating_count = m.group(1)
            break
    data["rating_count"] = rating_count

    # 星级
    star_el = item.select_one("[class*=a-icon-alt]")
    data["stars"] = ""
    if star_el:
        text = star_el.get_text(strip=True)
        m = re.search(r"(\d+\.?\d*)\s*颗星", text)
        if m:
            data["stars"] = m.group(1)

    # 月销量 "过去一个月有XXX顾客购买"
    monthly = ""
    for el in item.select("span, div"):
        text = el.get_text(strip=True)
        if "过去一个月" in text and "顾客购买" in text:
            m = re.search(r"过去一个月[有超过]?[\d,.]+万?\+?[名位]?顾客购买", text)
            if m:
                monthly = m.group()
            break
    data["monthly_sales"] = monthly

    # 链接
    link_el = item.select_one("a[href*='/dp/']")
    href = link_el.get("href", "") if link_el else ""
    if href.startswith("http"):
        data["link"] = href
    elif href.startswith("/"):
        data["link"] = f"https://www.amazon.com{href}"
    else:
        data["link"] = href

    data["scrape_time"] = scrape_time
    return data if data.get("title") else None


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取搜索结果。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = [_parse_item(item, scrape_time)
               for item in soup.select("div[data-asin]")]
    results = [r for r in results if r]
    if limit:
        results = results[:limit]
    return results


def from_search(keyword: str, limit: int = None) -> list[dict]:
    """在线搜索亚马逊商品（curl_cffi TLS 伪装）。"""
    from curl_cffi import requests as cr

    url = f"https://www.amazon.com/s?k={keyword}"
    resp = cr.get(url, impersonate="chrome124", timeout=15,
                  headers={"User-Agent": "Mozilla/5.0",
                           "Accept-Language": "zh-CN,zh;q=0.9"})
    if resp.status_code != 200:
        print(f"请求失败: HTTP {resp.status_code}")
        return []

    # 保存 HTML
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / f"Amazon_{keyword}.html"
    html_path.write_text(resp.text, encoding="utf-8")

    soup = BeautifulSoup(resp.text, "lxml")
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = [_parse_item(item, scrape_time)
               for item in soup.select("div[data-asin]")]
    results = [r for r in results if r]
    if limit:
        results = results[:limit]
    return results
