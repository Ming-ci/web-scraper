"""B站排行榜数据 CSV 持久化（薄 adapter，逻辑在 common.storage）。"""
from common.storage import append_csv

CSV_COLUMNS = ["title", "author", "plays", "likes", "category", "link", "cover", "rank", "scrape_time"]


def save(data: list[dict], filepath: str = "data/bilibili.csv") -> int:
    """排行榜数据追加写入 CSV，按 (标题, 分区) 去重。

    Returns:
        新增行数
    """
    return append_csv(data, CSV_COLUMNS, filepath, dedup_keys=["title", "category"])
