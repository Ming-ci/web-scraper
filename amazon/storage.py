"""CSV + Excel 导出。"""

import csv
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = ["asin", "title", "price", "stars", "rating_count",
               "monthly_sales", "link", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def to_csv(data: list[dict], filepath: str = None) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"amazon_{ts}.csv")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for d in data:
            writer.writerow({k: d.get(k, "") for k in CSV_COLUMNS})
    return filepath


def to_excel(data: list[dict], filepath: str = None) -> str:
    from openpyxl import Workbook

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"amazon_{ts}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "搜索结果"
    ws.append(["序号", "ASIN", "标题", "价格", "评分", "评价人数",
               "月销量", "链接", "抓取时间"])

    for i, d in enumerate(data, 1):
        ws.append([i, d.get("asin", ""), d.get("title", ""), d.get("price", ""),
                    d.get("stars", ""), d.get("rating_count", ""),
                    d.get("monthly_sales", ""), d.get("link", ""),
                    d.get("scrape_time", "")])

    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 60
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 8
    ws.column_dimensions["F"].width = 10
    ws.column_dimensions["G"].width = 20
    ws.column_dimensions["H"].width = 80
    ws.column_dimensions["I"].width = 20

    wb.save(filepath)
    return filepath
