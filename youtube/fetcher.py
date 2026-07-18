"""YouTube频道视频爬虫 — 本地HTML + 在线双模式。

DOM: ytd-video-renderer > a#video-title
"""
import re
from datetime import datetime
from bs4 import BeautifulSoup


def _parse_item(item, scrape_time: str) -> dict | None:
    """解析 ytd-rich-item-renderer 提取视频信息。"""
    # 标题+链接
    title_el = item.select_one("a#video-title")
    if not title_el:
        return None
    title = title_el.get("title", "") or title_el.get_text(strip=True)
    href = title_el.get("href", "")
    if href:
        href = href.split("&pp=")[0]
        link = f"https://www.youtube.com{href}" if href.startswith("/") else href
    else:
        link = ""

    # 所有文本片段（用于定位时长/观看/时间）
    text = item.get_text("|||", strip=True)
    parts = [p.strip() for p in text.split("|||") if p.strip()]

    # 时长：第一个形如 "MM:SS" 或 "H:MM:SS" 的片段
    duration = ""
    for p in parts:
        if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", p):
            duration = p
            break

    # 观看数："X万次观看" 或 "X次观看" 或 "X views"
    views = ""
    for p in parts:
        if "次观看" in p or re.match(r"^[\d,.]+[万]?(次观看|views)", p):
            m = re.search(r"([\d,.]+万?次观看|[\d,.]+万? views)", p)
            if m:
                views = m.group(1)
                break
    if not views:
        for p in parts:
            if "views" in p.lower():
                views = p
                break

    # 发布时间："X天前"、"X小时前"、"X周前"、"X个月前"、"X年前"
    pub_time = ""
    for p in parts:
        if re.search(r"\d+\s*[天小周月年]时?前", p):
            pub_time = p
            break

    # 频道ID
    channel = ""
    for a in item.select("a[href*='/@']"):
        t = a.get_text(strip=True)
        if t and len(t) < 50:
            channel = t
            break

    return {
        "title": title,
        "views": views,
        "pub_time": pub_time,
        "duration": duration,
        "link": link,
        "channel": channel,
        "scrape_time": scrape_time,
    }


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results = []
    seen = set()

    for item in soup.select("ytd-video-renderer"):
        data = _parse_item(item, scrape_time)
        if data and data["title"] and data["link"] not in seen:
            seen.add(data["link"])
            results.append(data)

    if limit:
        results = results[:limit]
    return results


def from_channel(channel_id: str, count: int = 30, proxy: str = None) -> list[dict]:
    """在线爬取 YouTube 频道视频（yt-dlp 引擎）。

    使用 yt-dlp 内部提取器，零反爬成本获取完整字段。
    """
    import yt_dlp

    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proxy_arg = proxy or "http://127.0.0.1:7890"
    url = f"https://www.youtube.com/@{channel_id}/videos" if not channel_id.startswith("UC") else \
          f"https://www.youtube.com/channel/{channel_id}/videos"

    opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "playlistend": count,
        "proxy": proxy_arg,
    }

    def _fmt_duration(sec):
        if not sec: return ""
        m, s = divmod(int(sec), 60)
        return f"{m}:{s:02d}" if m < 60 else f"{m//60}:{m%60:02d}:{s:02d}"

    def _fmt_views(n):
        if not n: return ""
        return f"{n:,}次观看" if isinstance(n, int) else str(n)

    results = []
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            channel_name = info.get("channel", channel_id)
            for entry in info.get("entries", []) or []:
                results.append({
                    "title": entry.get("title", ""),
                    "views": _fmt_views(entry.get("view_count")),
                    "pub_time": "",  # flat模式不含日期，需单页抓取
                    "duration": _fmt_duration(entry.get("duration")),
                    "link": entry.get("url", "") or f"https://www.youtube.com/watch?v={entry.get('id','')}",
                    "channel": entry.get("channel", channel_name),
                    "scrape_time": scrape_time,
                })
    except Exception as e:
        print(f"yt-dlp 失败: {e}")

    return results
