"""淘宝商品 CSV + Excel 导出（薄 adapter，逻辑在 common.storage）。"""
from datetime import datetime
from pathlib import Path

from common.storage import to_csv as _to_csv
from common.storage import to_excel as _to_excel

CSV_COLUMNS = ["title", "brand", "price", "sales", "shop", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "taobao"


def _path(ext: str) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return str(OUTPUT_DIR / f"taobao_{datetime.now():%Y%m%d_%H%M%S}.{ext}")


def to_csv(data, fp=None):
    return _to_csv(data, CSV_COLUMNS, fp or _path("csv"), numbered=True)


def to_excel(data, fp=None):
    return _to_excel(
        data, CSV_COLUMNS,
        ["标题", "品牌", "价格", "销量", "店铺", "爬取时间"],
        fp or _path("xlsx"), sheet_title="商品",
        col_widths={"A": 6, "B": 55, "C": 18, "D": 10, "E": 12, "F": 22, "G": 20},
    )
