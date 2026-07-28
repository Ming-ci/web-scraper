"""CSV + Excel 导出。"""
import csv
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = ["title", "price", "sales", "shop", "link", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def to_csv(data, fp=None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fp = fp or str(OUTPUT_DIR / f"taobao_{datetime.now():%Y%m%d_%H%M%S}.csv")
    with open(fp, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS); w.writeheader()
        for d in data: w.writerow({k: d.get(k, "") for k in CSV_COLUMNS})
    return fp


def to_excel(data, fp=None):
    from openpyxl import Workbook
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fp = fp or str(OUTPUT_DIR / f"taobao_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "商品"
    ws.append(["序号", "标题", "价格", "销量", "店铺", "链接", "爬取时间"])
    for i, d in enumerate(data, 1):
        ws.append([i, d.get("title", ""), d.get("price", ""), d.get("sales", ""),
                    d.get("shop", ""), d.get("link", ""), d.get("scrape_time", "")])
    ws.column_dimensions["A"].width = 6; ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 10; ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 20; ws.column_dimensions["F"].width = 60
    ws.column_dimensions["G"].width = 20
    wb.save(fp)
    return fp
