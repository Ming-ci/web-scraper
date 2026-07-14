"""亚马逊搜索爬虫 — 本地 HTML 解析。

DOM 结构: div[data-asin]（过滤 data-asin='' 的占位元素）
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取搜索结果。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items = soup.select("div[data-asin]")
    results = []

    for item in items:
        asin = item.get("data-asin", "").strip()
        if not asin:
            continue  # 占位 div

        data = {"asin": asin}

        # 标题
        h2 = item.select_one("h2")
        data["title"] = h2.get_text(strip=True) if h2 else ""

        # 价格 — span.a-price 内
        price_whole = item.select_one(".a-price-whole")
        price_fraction = item.select_one(".a-price-fraction")
        price_symbol = item.select_one(".a-price-symbol")
        if price_whole:
            price = price_whole.get_text(strip=True)
            if price_fraction:
                price += "." + price_fraction.get_text(strip=True)
            symbol = price_symbol.get_text(strip=True) if price_symbol else ""
            data["price"] = f"{symbol} {price}" if symbol else price
            # 清理 JPY 后多余的重复数字
            if "JPY" in data["price"]:
                parts = data["price"].split("JPY")
                if len(parts) > 1:
                    data["price"] = f"JPY {parts[1].strip().split()[0]}"
        else:
            # 无价格可能是多变体商品，尝试从文本提取
            price_text = ""
            for el in item.select("span"):
                t = el.get_text(strip=True)
                if re.match(r"^(JPY|USD|EUR|GBP|¥|$)\s*[\d,]+", t):
                    price_text = t
                    break
            data["price"] = price_text

                # 评分人数 — 文本如 "(3016)" 或 "(2.4万)"
        rating_count = ""
        for el in item.select("span"):
            text = el.get_text(strip=True)
            m = re.match(r"^\(([\d,.]+万?)\)$", text)
            if m:
                rating_count = m.group(1)
                break
        data["rating_count"] = rating_count

        # 星级 — i.a-icon-star-mini 或 span 含 "星"
        star_el = item.select_one("[class*=a-icon-alt]")
        data["stars"] = ""
        if star_el:
            text = star_el.get_text(strip=True)
            m = re.search(r"(\d+\.?\d*)\s*颗星", text)
            if m:
                data["stars"] = m.group(1)

                # 月销量 — 精确提取 "过去一个月有XXX顾客购买"
        monthly = ""
        for el in item.select("span, div"):
            text = el.get_text(strip=True)
            if "过去一个月" in text and "顾客购买" in text:
                # 只取"过去一个月有..."这部分
                m = re.search(r"过去一个月[有超过]?[\d,.]+万?\+?[名位]?顾客购买", text)
                if m:
                    monthly = m.group()
                else:
                    monthly = text
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

        if data["title"]:
            results.append(data)

    if limit:
        results = results[:limit]
    return results
