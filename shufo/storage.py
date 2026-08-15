"""佛书网书籍 CSV + Excel 导出（薄 adapter，逻辑在 common.storage）。"""
from datetime import datetime
from pathlib import Path

from common.storage import to_csv as _to_csv
from common.storage import to_excel as _to_excel

CSV_COLUMNS = ["title", "pages", "size", "pub_time", "rating", "beans", "link", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def _path(ext: str) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return str(OUTPUT_DIR / f"shufo_{datetime.now():%Y%m%d_%H%M%S}.{ext}")


def to_csv(data: list[dict], filepath: str = None) -> str:
    return _to_csv(data, CSV_COLUMNS, filepath or _path("csv"))


def to_excel(data: list[dict], filepath: str = None) -> str:
    return _to_excel(
        data, CSV_COLUMNS,
        ["名称", "页数", "大小", "时间", "评分", "书豆", "链接", "抓取时间"],
        filepath or _path("xlsx"), sheet_title="文档列表",
        col_widths={"A": 6, "B": 70, "C": 8, "D": 10, "E": 10,
                    "F": 8, "G": 8, "H": 45, "I": 20},
    )
