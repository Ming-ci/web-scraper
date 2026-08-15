"""小红书笔记 CSV + Excel 导出（薄 adapter，逻辑在 common.storage）。"""
from datetime import datetime
from pathlib import Path

from common.storage import to_csv as _to_csv
from common.storage import to_excel as _to_excel

CSV_COLUMNS = ["title", "author", "pub_time", "likes", "link", "cover", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def _path(ext: str) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return str(OUTPUT_DIR / f"xiaohongshu_{datetime.now():%Y%m%d_%H%M%S}.{ext}")


def to_csv(data: list[dict], filepath: str = None) -> str:
    # 保持原语义：CSV 按 link 去重
    return _to_csv(data, CSV_COLUMNS, filepath or _path("csv"), dedup_key="link")


def to_excel(data: list[dict], filepath: str = None) -> str:
    return _to_excel(
        data, CSV_COLUMNS,
        ["标题", "博主", "发布时间", "点赞数", "链接", "封面图", "抓取时间"],
        filepath or _path("xlsx"), sheet_title="搜索结果",
        col_widths={"A": 6, "B": 55, "C": 16, "D": 10, "E": 10,
                    "F": 40, "G": 45, "H": 20},
    )
