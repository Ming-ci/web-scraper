"""YouTube 视频 CSV + Excel 导出（薄 adapter，逻辑在 common.storage）。"""
from datetime import datetime
from pathlib import Path

from common.storage import to_csv as _to_csv
from common.storage import to_excel as _to_excel

CSV_COLUMNS = ["title", "views", "pub_time", "duration", "link", "channel", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def _path(ext: str) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return str(OUTPUT_DIR / f"youtube_{datetime.now():%Y%m%d_%H%M%S}.{ext}")


def to_csv(data: list[dict], filepath: str = None) -> str:
    return _to_csv(data, CSV_COLUMNS, filepath or _path("csv"))


def to_excel(data: list[dict], filepath: str = None) -> str:
    return _to_excel(
        data, CSV_COLUMNS,
        ["标题", "播放量", "发布时间", "时长", "链接", "频道", "爬取时间"],
        filepath or _path("xlsx"), sheet_title="视频",
        col_widths={"A": 6, "B": 60, "C": 12, "D": 10, "E": 8,
                    "F": 50, "G": 20, "H": 20},
    )
