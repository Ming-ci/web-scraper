"""X(Twitter) 推文爬虫 — Playwright 动态渲染。
DOM: article[data-testid=\"tweet\"]
"""

from datetime import datetime
from bs4 import BeautifulSoup


def _parse_tweet(article, scrape_time: str) -> dict | None:
    try:
        # 用户名
        uname = article.select_one('[data-testid="User-Name"]')
        author = uname.get_text(strip=True) if uname else ""

        # 推文内容
        body = article.select_one('[data-testid="tweetText"]')
        text = body.get_text(strip=True) if body else ""

        # 时间
        time_el = article.select_one("time")
        pub_time = time_el.get("datetime", "") if time_el else ""

        # 链接
        link = ""
        for a in article.select('a[href*="/status/"]'):
            href = a.get("href", "")
            if href.startswith("/"):
                link = f"https://x.com{href}"
            else:
                link = href
            break

        # 互动数据
        replies = _get_stat(article, "reply")
        retweets = _get_stat(article, "retweet")
        likes = _get_stat(article, "like")

        # 浏览量
        views = ""
        view_el = article.select_one('a[href$="/analytics"]')
        if view_el:
            views = view_el.get_text(strip=True)

        if not text:
            return None

        return {
            "author": author,
            "text": text,
            "pub_time": pub_time,
            "link": link,
            "replies": replies,
            "retweets": retweets,
            "likes": likes,
            "views": views,
            "scrape_time": scrape_time,
        }
    except Exception:
        return None


def _get_stat(article, testid: str) -> str:
    el = article.select_one(f'[data-testid="{testid}"]')
    if not el:
        return ""
    val = el.get_text(strip=True)
    if val:
        return val
    return el.get("aria-label", "")


def from_user(username: str, count: int = 20) -> list[dict]:
    """爬取指定用户的推文（Playwright + Cookie 登录态）。"""
    from playwright.sync_api import sync_playwright
    from twitter.auth import load_cookies, has_cookies

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = f"https://x.com/{username}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        if has_cookies():
            formatted = [{"name": k, "value": v, "domain": ".x.com", "path": "/"}
                         for k, v in load_cookies().items()]
            context.add_cookies(formatted)

        page = context.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)

        # 滚动加载更多
        articles = []
        for _ in range(max(count // 5, 5)):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            current = page.locator('article[data-testid="tweet"]').all()
            if len(current) >= count:
                break

        soup = BeautifulSoup(page.content(), "lxml")
        articles = soup.select('article[data-testid="tweet"]')
        browser.close()

    results = []
    seen = set()
    for article in articles:
        data = _parse_tweet(article, scrape_time)
        if data and data["text"] and data["link"] not in seen:
            seen.add(data["link"])
            results.append(data)

    return results[:count]
