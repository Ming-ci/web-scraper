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

    prices = [el.get_text(strip=True) for el in soup.select("[class*=priceInt]")]
    shops  = [el.get_text(strip=True) for el in soup.select("[class*=shopNameText]")]
    sales  = [el.get_text(strip=True) for el in soup.select("[class*=realSales]")]
    links  = [a.get("href","").replace("&amp;","&") for a in
              soup.select("a[href*=\"item.taobao\"], a[href*=\"detail.tmall\"]")]

    results = []
    for i in range(len(prices)):
        results.append({
            "title": titles[i] if i < len(titles) else "",
            "price": prices[i],
            "shop":  shops[i] if i < len(shops) else "",
            "sales": sales[i] if i < len(sales) else "",
            "link":  links[i] if i < len(links) else "",
            "scrape_time": scrape_time,
        })

    if limit:
        results = results[:limit]
    return results
