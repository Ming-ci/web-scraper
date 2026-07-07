"""RSS 爬虫 — 从 YAML 配置的 tier1 源采集标题和摘要。

输出 data/raw/YYYY-MM-DD.json 格式：
    [{title, link, summary, source, category, published, fetched_at}]
"""

import json
from datetime import datetime
from pathlib import Path

import feedparser
import httpx
import yaml

from common.headers import get_headers

CONFIG_PATH = Path(__file__).parent.parent / "config" / "sources.yaml"
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


def _load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def crawl() -> list[dict]:
    """抓取所有 tier1 RSS 源，返回标题+摘要列表。"""
    config = _load_config()
    sources = config["sources"]
    settings = config["settings"]
    max_per = settings.get("max_per_source", 20)

    all_items = []
    headers = dict(get_headers())
    headers["User-Agent"] = settings.get(
        "user_agent", "Mozilla/5.0 (compatible; NewsBot/1.0)"
    )

    for src in sources:
        name = src["name"]
        url = src["url"]
        category = src["category"]
        print(f"  {name} ({category})...", end=" ", flush=True)

        try:
            resp = httpx.get(url, headers=headers, timeout=settings.get("request_timeout", 15),
                             follow_redirects=True)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
        except Exception as e:
            print(f"失败: {e}")
            continue

        count = 0
        for entry in feed.entries[:max_per]:
            item = {
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "summary": entry.get("summary", "").strip()[:500],
                "source": name,
                "category": category,
                "published": entry.get("published", ""),
                "fetched_at": datetime.now().isoformat(),
            }
            all_items.append(item)
            count += 1
        print(f"{count} 条")

    return all_items


def save_raw(items: list[dict]) -> str:
    """保存原始采集数据到 data/raw/YYYY-MM-DD.json，返回文件路径。"""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    filepath = RAW_DIR / f"{today}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

    return str(filepath)
