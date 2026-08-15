"""淘宝/天猫搜索爬虫 — 以 price 为锚点，向上找 title。"""
from datetime import datetime
from bs4 import BeautifulSoup

from taobao.brand_map import extract_brand


def parse(html: str, limit: int = None) -> list[dict]:
    """从搜索页 HTML 提取商品列表（纯函数，无 IO）。

    Args:
        html: 搜索页 HTML 文本
        limit: 最多返回条数

    Returns:
        list[dict]，每项含 title/brand/price/shop/sales/scrape_time
    """
    soup = BeautifulSoup(html, "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    titles = [el.get_text(strip=True) for el in soup.select("[class*=title--ASSt27UY]")]
    # fallback
    if not titles:
        titles = [el.get_text(strip=True) for el in soup.select("[class*=title--]")
                  if len(el.get_text(strip=True)) > 15]

    price_els = soup.select("[class*=priceInt]")
    titles = titles[:len(price_els)] if len(titles) >= len(price_els) else titles + [""] * (len(price_els) - len(titles))
    shops = [el.get_text(strip=True) for el in soup.select("[class*=shopNameText]")]
    sales = [el.get_text(strip=True) for el in soup.select("[class*=realSales]")]

    results = []
    for i in range(len(price_els)):
        results.append({
            "title": titles[i],
            "brand": extract_brand(titles[i]),
            "price": price_els[i].get_text(strip=True),
            "shop": shops[i] if i < len(shops) else "",
            "sales": sales[i] if i < len(sales) else "",
            "scrape_time": scrape_time,
        })

    if limit:
        results = results[:limit]
    return results


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取商品列表（IO 薄壳，解析在 parse）。"""
    with open(filepath, encoding="utf-8") as f:
        return parse(f.read(), limit=limit)
