"""淘宝/天猫搜索爬虫 — 以 price 为锚点，向上找 title。"""
import re
from datetime import datetime
from bs4 import BeautifulSoup

# 品牌映射：各种写法 → 统一品牌名
BRAND_MAP = {
    # 耐克
    "nike": "Nike/耐克", "耐克": "Nike/耐克", "NIKE": "Nike/耐克",
    # 阿迪达斯
    "adidas": "Adidas/阿迪达斯", "阿迪达斯": "Adidas/阿迪达斯", "阿迪": "Adidas/阿迪达斯",
    "三叶草": "Adidas/阿迪达斯",
    # 361度
    "361": "361°", "361°": "361°", "361度": "361°",
    # 匹克
    "匹克": "匹克/PEAK", "peak": "匹克/PEAK", "PEAK": "匹克/PEAK",
    # 安踏
    "安踏": "安踏/ANTA", "anta": "安踏/ANTA", "ANTA": "安踏/ANTA",
    # 李宁
    "李宁": "李宁/Li-Ning", "li-ning": "李宁/Li-Ning", "lining": "李宁/Li-Ning",
    # 特步
    "特步": "特步/Xtep", "xtep": "特步/Xtep",
    # 鸿星尔克
    "鸿星尔克": "鸿星尔克/ERKE", "erke": "鸿星尔克/ERKE",
    # New Balance
    "new balance": "New Balance", "nb": "New Balance", "新百伦": "New Balance",
    "newbalance": "New Balance",
    # 亚瑟士
    "asics": "ASICS/亚瑟士", "亚瑟士": "ASICS/亚瑟士",
    # 斯凯奇
    "skechers": "Skechers/斯凯奇", "斯凯奇": "Skechers/斯凯奇",
    # 彪马
    "puma": "PUMA/彪马", "彪马": "PUMA/彪马",
    # 回力
    "回力": "回力/Warrior", "warrior": "回力/Warrior",
    # 乔丹
    "乔丹": "乔丹", "jordan": "乔丹",
    # 斐乐
    "fila": "FILA/斐乐", "斐乐": "FILA/斐乐",
    # 锐步
    "reebok": "Reebok/锐步", "锐步": "Reebok/锐步",
    # 匡威
    "converse": "Converse/匡威", "匡威": "Converse/匡威",
    # 万斯
    "vans": "VANS/万斯", "万斯": "VANS/万斯",
    # 美津浓
    "mizuno": "Mizuno/美津浓", "美津浓": "Mizuno/美津浓",
    # 索康尼
    "saucony": "Saucony/索康尼", "索康尼": "Saucony/索康尼",
    # 鬼冢虎
    "onitsuka": "Onitsuka Tiger/鬼冢虎", "鬼冢虎": "Onitsuka Tiger/鬼冢虎",
    # 安德玛
    "under armour": "Under Armour/安德玛", "安德玛": "Under Armour/安德玛",
    "ua": "Under Armour/安德玛",
    # 萨洛蒙
    "salomon": "Salomon/萨洛蒙", "萨洛蒙": "Salomon/萨洛蒙",
    # Hoka
    "hoka": "HOKA", "hoka one one": "HOKA",
    # 多威
    "多威": "多威/Do-win",
    # Brooks
    "brooks": "Brooks/布鲁克斯", "布鲁克斯": "Brooks/布鲁克斯",
    # 必迈
    "必迈": "必迈/bmai", "bmai": "必迈/bmai",
    # 马孔多
    "马孔多": "马孔多",
    # 骆驼
    "骆驼": "骆驼/Camel", "camel": "骆驼/Camel",
    # 探路者
    "探路者": "探路者/Toread", "toread": "探路者/Toread",
    # 凯乐石
    "凯乐石": "凯乐石/Kailas", "kailas": "凯乐石/Kailas",
}


def _extract_brand(title: str) -> str:
    """从商品标题中提取品牌。"""
    title_lower = title.lower()
    for keyword, brand in BRAND_MAP.items():
        if keyword.lower() in title_lower:
            return brand
    return "其他"


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
            "brand": _extract_brand(titles[i]),
            "price": price_els[i].get_text(strip=True),
            "shop":  shops[i] if i < len(shops) else "",
            "sales": sales[i] if i < len(sales) else "",
            "scrape_time": scrape_time,
        })

    if limit:
        results = results[:limit]
    return results
