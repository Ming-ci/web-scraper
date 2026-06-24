"""B站热门视频爬虫 —— Playwright 浏览器自动化 + BeautifulSoup 解析。

页面: https://www.bilibili.com/v/popular/all
DOM 结构（.video-card）:
    a                    — 视频链接（href）
    img                  — 封面图（src）
    p.video-name         — 标题（title 属性含完整标题）
    .up-name__text       — UP 主名称
    .play-text           — 播放量（如 "52.6万"）
    .like-text           — 点赞数（如 "588"）

JS 动态渲染 —— requests 无法获取，必须用 Playwright。
"""

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URL = "https://www.bilibili.com/v/popular/all"


def _parse_card(card) -> dict | None:
    """从单个 video-card 提取视频信息。"""
    # 标题
    title_el = card.select_one("p.video-name")
    title = title_el.get("title", "") or title_el.get_text(strip=True) if title_el else ""

    # UP 主
    up_el = card.select_one(".up-name__text")
    author = up_el.get_text(strip=True) if up_el else ""

    # 播放量（span.play-text 内的纯文本）
    play_el = card.select_one(".play-text")
    plays = ""
    if play_el:
        plays = play_el.get_text(strip=True)

    # 点赞数
    like_el = card.select_one(".like-text")
    likes = ""
    if like_el:
        likes = like_el.get_text(strip=True)

    # 视频链接
    link_el = card.select_one("a")
    link = ""
    if link_el and link_el.get("href"):
        href = link_el["href"]
        link = f"https:{href}" if href.startswith("//") else href

    # 封面图
    img_el = card.select_one("img")
    cover = ""
    if img_el:
        cover = img_el.get("src") or img_el.get("data-src") or ""
        if cover.startswith("//"):
            cover = f"https:{cover}"

    if not title:
        return None

    return {
        "title": title.strip(),
        "author": author.strip(),
        "plays": plays.strip(),
        "likes": likes.strip(),
        "link": link.strip(),
        "cover": cover.strip(),
    }


def fetch_page(scroll_times: int = 3) -> list[dict]:
    """用 Playwright 打开 B 站热门页，滚动加载更多，提取全部视频卡片。

    Args:
        scroll_times: 滚动次数（每次加载约 20 个视频）

    Returns:
        视频列表
    """
    results = []
    card_links = set()  # 按链接去重

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)  # 额外等待二次渲染

        # 滚动加载更多
        for i in range(scroll_times):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)  # 等新卡片渲染

        # 解析
        soup = BeautifulSoup(page.content(), "lxml")
        cards = soup.select(".video-card")

        for card in cards:
            data = _parse_card(card)
            if data and data["link"] not in card_links:
                card_links.add(data["link"])
                results.append(data)

        browser.close()

    return results
