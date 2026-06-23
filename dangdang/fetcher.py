"""当当网搜索页抓取 + BeautifulSoup 解析。

页面结构: ul.bigimg > li — 每个 li 是一个商品卡片
    p.name > a  — 书名（title 属性含完整标题）
    .search_now_price — 当前价格
    .search_comment_num — 评论数
    a.pic — 商品链接（href 属性，相对路径）

编码: GBK
分页: ?key=XXX&page_index=N
"""

import sys
import re

from bs4 import BeautifulSoup

from common.session import create_session
from common.throttle import random_delay
from common.proxy import get_proxies
from common.retry import retry_on_network_error

BASE_URL = "http://search.dangdang.com/"

CSV_COLUMNS = ["title", "price", "comments", "link"]


def _parse_item(li) -> dict | None:
    """解析单个 li 商品卡片，提取书名/价格/评论/链接。

    Returns:
        dict 包含 title, price, comments, link；解析异常返回 None
    """
    # 书名
    title_el = li.select_one("p.name > a")
    title = ""
    if title_el:
        title = title_el.get("title", "") or title_el.get_text(strip=True)

    # 价格
    price_el = li.select_one(".search_now_price")
    price = price_el.get_text(strip=True) if price_el else ""

    # 评论数
    comment_el = li.select_one(".search_comment_num")
    comments = comment_el.get_text(strip=True) if comment_el else ""

    # 商品链接（补全为完整 URL）
    link_el = li.select_one("a.pic") or li.select_one("p.name a")
    link = ""
    if link_el and link_el.get("href"):
        href = link_el["href"]
        link = f"http:{href}" if href.startswith("//") else href

    if not title:
        return None

    return {
        "title": title.strip(),
        "price": price.strip(),
        "comments": comments.strip(),
        "link": link.strip(),
    }


@retry_on_network_error(max_retries=2, base_delay=1.0)
def fetch_page(keyword: str, page: int = 1) -> list[dict]:
    """抓取当当搜索结果的指定页。

    Args:
        keyword: 搜索关键词
        page: 页码，从 1 开始

    Returns:
        商品列表，每个商品为 dict

    Raises:
        ConnectionError: 网络不可达
        RuntimeError: HTTP 非 200
        ValueError: 页面结构与预期不符
    """
    session = create_session()
    url = f"{BASE_URL}?key={keyword}&act=input"
    if page > 1:
        url += f"&page_index={page}"

    response = session.get(url, proxies=get_proxies(), timeout=10)

    if response.status_code != 200:
        raise RuntimeError(f"请求失败，HTTP 状态码：{response.status_code}")

    # 当当编码为 GBK
    response.encoding = "gbk"
    soup = BeautifulSoup(response.text, "lxml")

    items = soup.select("ul.bigimg > li")
    if not items:
        raise ValueError("页面未找到商品列表 ul.bigimg > li，页面结构可能已变化。")

    results = []
    for li in items:
        data = _parse_item(li)
        if data:
            results.append(data)

    return results


def fetch_all(keyword: str, max_pages: int = 5) -> list[dict]:
    """抓取多页搜索结果。

    Args:
        keyword: 搜索关键词
        max_pages: 最多抓取页数，默认 5

    Returns:
        所有商品列表（扁平化）
    """
    all_data = []
    for page in range(1, max_pages + 1):
        if page > 1:
            random_delay(1.0, 2.0)  # 翻页间隔

        print(f"  第 {page}/{max_pages} 页...", end=" ", flush=True)
        try:
            data = fetch_page(keyword, page)
            all_data.extend(data)
            print(f"{len(data)} 条")
        except (ConnectionError, RuntimeError, ValueError) as e:
            print(f"失败：{e}")
            continue

    return all_data
