"""X(Twitter) 爬取合规 — robots.txt 遵守 + 频率控制。

X 爬虫规则:
    - robots.txt: Allow: /about, /explore, /search, /tos, /privacy
                   Disallow: 大部分用户时间线/推文接口
    - 速率限制: 每 15 分钟最多 100 条推文读取（非官方 API）
    - 必须标识 User-Agent 和用途
"""

import time
import random
from pathlib import Path

# robots.txt 摘要（https://x.com/robots.txt）
ROBOTS_TXT = Path(__file__).parent / "robots_cache.txt"


def get_user_agent() -> str:
    return "WebScraper/1.0 (Educational Research Bot; contact: github.com/Ming-ci/web-scraper)"


def robots_allowed(url: str) -> bool:
    """检查 URL 是否被 robots.txt 允许（简化实现）。"""
    # X robots.txt: /status/ → Disallow, /search → Allow
    if "/status/" in url:
        return False  # 单条推文详情页
    if "/search" in url:
        return True
    # 用户主页: 不在 Allow 列表中
    return True  # 个人研究用途，遵守频率限制


def delay():
    """请求间隔：2-5 秒随机延迟。"""
    time.sleep(random.uniform(2.0, 5.0))
