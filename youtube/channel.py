"""YouTube 频道采集 — 深模块：一个接口，两个引擎 adapter。

对外只暴露 fetch_channel()，字段不变式在接口层声明并保证：
    title / views / pub_time / duration / link / channel / scrape_time 恒有值（可能为空串）。
引擎（yt-dlp / innertube）差异收敛在模块内部，调用方无需关心。
"""

from youtube.innertube import browse_channel as _browse_innertube

# 统一字段不变式：引擎返回缺失的字段在此补空，保证形状一致
_FIELDS = ("title", "views", "pub_time", "duration", "link", "channel", "scrape_time")


def _normalize(items: list[dict]) -> list[dict]:
    """补齐缺失字段，保证返回形状一致。"""
    return [{k: item.get(k, "") for k in _FIELDS} for item in items]


def _fetch_ytdlp(channel_id: str, count: int, proxy: str) -> list[dict]:
    from youtube.fetcher import from_channel
    return from_channel(channel_id, count=count, proxy=proxy)


def fetch_channel(channel_id: str, count: int = 30, proxy: str = None,
                  engine: str = "yt-dlp") -> list[dict]:
    """获取频道视频列表（统一字段）。

    Args:
        channel_id: @用户名 或 UCxxx 频道 ID
        count: 爬取条数
        proxy: HTTP 代理
        engine: "yt-dlp"（默认）或 "innertube"（纯 Python 逆向）

    Returns:
        视频数据列表，字段形状恒定

    Raises:
        ValueError: 未知引擎
    """
    if engine == "yt-dlp":
        items = _fetch_ytdlp(channel_id, count, proxy)
    elif engine == "innertube":
        items = _browse_innertube(channel_id, count=count, proxy=proxy)
    else:
        raise ValueError(f"未知引擎: {engine}，可选: yt-dlp / innertube")

    return _normalize(items)
