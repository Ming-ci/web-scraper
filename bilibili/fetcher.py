"""B站排行榜爬虫 —— Playwright 浏览器自动化 + BeautifulSoup 解析。

页面: https://www.bilibili.com/v/popular/rank
交互流程:
    1. 打开排行榜页
    2. 点击分区标签（如"科技"）切换分类
    3. 等待 100 个 li.rank-item 渲染
    4. 提取排名、标题、UP主、播放量、点赞数

DOM 结构（li.rank-item）:
    i.num         — 排名（1-100）
    a.title       — 视频标题
    a (第二个)     — UP 主名称
    span.data-box — 播放量 / 弹幕数（按顺序）
"""

from datetime import datetime

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 排行榜分区标签 → 中文名
CATEGORIES = {
    "all": "全站",
    "tech": "科技",
    "digital": "数码",
    "knowledge": "知识",
    "game": "游戏",
    "music": "音乐",
    "dance": "舞蹈",
    "film": "影视",
    "food": "美食",
    "fashion": "时尚",
    "car": "汽车",
    "sport": "运动",
}

RANK_URL = "https://www.bilibili.com/v/popular/rank"


def _click_tab(page, tab_name: str) -> bool:
    """点击排行榜分区标签。返回是否找到并点击成功。"""
    # 找 ul.rank-tab 内的所有 li，匹配文本
    tabs = page.locator("ul.rank-tab > li").all()
    for tab in tabs:
        text = tab.text_content().strip()
        if tab_name in text:
            tab.click()
            page.wait_for_timeout(2000)  # 等待 AJAX 加载新榜单
            return True
    return False


def _parse_item(li) -> dict | None:
    """从 li.rank-item 提取单个视频数据。

    DOM 实际结构:
        a (cover link, 空文本)
        a.title  — 标题
        a (space link) — UP 主名
        span.data-box[0] — UP 主名（重复）
        span.data-box[1] — 播放量
        span.data-box[2] — 点赞数
    """
    # 排名
    num_el = li.select_one("i.num")
    rank = int(num_el.get_text(strip=True)) if num_el else 0

    # 标题
    title_el = li.select_one("a.title")
    title = title_el.get_text(strip=True) if title_el else ""

    # data-box 数组
    data_spans = li.select("span.data-box")
    plays = data_spans[1].get_text(strip=True) if len(data_spans) >= 2 else ""
    likes = data_spans[2].get_text(strip=True) if len(data_spans) >= 3 else ""

    # UP 主 — 取 data-box[0] 或第三个 a 标签
    author = data_spans[0].get_text(strip=True) if len(data_spans) >= 1 else ""
    if not author:
        # fallback：通过 space.bilibili.com 链接找到 UP 主 a 标签
        for a in li.select("a"):
            href = a.get("href", "")
            if "space.bilibili.com" in href:
                author = a.get_text(strip=True)
                break

    if not title:
        return None

    return {
        "title": title.strip(),
        "author": author.strip(),
        "plays": plays.strip(),
        "likes": likes.strip(),
        "rank": rank,
    }



def fetch_rank(category: str = "tech") -> list[dict]:
    """用 Playwright 抓取 B 站排行榜指定分区的前 100 个视频。

    Args:
        category: 分区 key（all/tech/digital/knowledge/game/music/...）

    Returns:
        视频列表，含 title/author/plays/likes/rank
    """
    tab_name = CATEGORIES.get(category, category)
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_viewport_size({"width": 1280, "height": 900})

        # 1. 打开排行榜页
        page.goto(RANK_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(2000)

        # 2. 点击目标分区标签
        if category != "all":
            if _click_tab(page, tab_name):
                print(f"  已切换到「{tab_name}」分区")
            else:
                print(f"  ⚠ 未找到「{tab_name}」标签，使用默认分区")

        # 3. 等待排行榜加载
        page.wait_for_selector("li.rank-item", timeout=10000)
        page.wait_for_timeout(1000)

        # 4. 解析
        soup = BeautifulSoup(page.content(), "lxml")
        items = soup.select("li.rank-item")

        results = []
        for li in items:
            data = _parse_item(li)
            if data:
                data["scrape_time"] = scrape_time
                data["category"] = tab_name
                results.append(data)

        browser.close()

    return results
