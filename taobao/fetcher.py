"""淘宝/天猫搜索爬虫 — 以 price 为锚点，向上找 title。"""
import re
from datetime import datetime
from bs4 import BeautifulSoup


def from_file(filepath: str, limit: int = None) -> list[dict]:
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    titles = [el.get_text(strip=True) for el in soup.select("[class*=title--ASSt27UY]")]
    # fallback
    if not titles:
        titles = [el.get_text(strip=True) for el in soup.select("[class*=title--]")
                  if len(el.get_text(strip=True)) > 15]

    price_els = soup.select("[class*=priceInt]")
    titles = titles[:len(price_els)] if len(titles) >= len(price_els) else titles + [""] * (len(price_els) - len(titles))
    shops  = [el.get_text(strip=True) for el in soup.select("[class*=shopNameText]")]
    sales  = [el.get_text(strip=True) for el in soup.select("[class*=realSales]")]
    link_els = [a for a in soup.select("a[target=\"_blank\"]")
                if ("item.taobao" in a.get("href","") or "detail.tmall" in a.get("href",""))
                and "simba" not in a.get("href","")]

    # 为每个价格匹配最近的链接（按 DOM 先后顺序对齐）
    # 策略：遍历价格列表，为每个价格找 DOM 中下一个链接
    link_idx = 0
    results = []
    for i in range(len(price_els)):
        link = ""
        if link_idx < len(link_els):
            link = link_els[link_idx].get("href", "").replace("&amp;", "&")
            link_idx += 1  # 每个链接只分配给一个价格

        results.append({
            "title": titles[i],
            "price": price_els[i].get_text(strip=True),
            "shop":  shops[i] if i < len(shops) else "",
            "sales": sales[i] if i < len(sales) else "",
            "link":  link,
            "scrape_time": scrape_time,
        })

    if limit:
        results = results[:limit]
    return results
