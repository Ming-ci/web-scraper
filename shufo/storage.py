"""CSV + Excel 导出。"""

from datetime import datetime
from pathlib import Path
import csv

CSV_COLUMNS = ["title", "pages", "size", "pub_time", "rating", "beans", "link", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def to_csv(data: list[dict], filepath: str = None) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"shufo_{ts}.csv")
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
        filepath = str(OUTPUT_DIR / f"shufo_{ts}.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "文档列表"
    ws.append(["序号", "名称", "页数", "大小", "时间", "评分", "书豆", "链接", "爬取时间"])
    for i, d in enumerate(data, 1):
        ws.append([i, d.get("title", ""), d.get("pages", ""), d.get("size", ""),
                    d.get("pub_time", ""), d.get("rating", ""), d.get("beans", ""),
                    d.get("link", ""), d.get("scrape_time", "")])
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 70
    ws.column_dimensions["C"].width = 8
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 8
    ws.column_dimensions["G"].width = 8
    ws.column_dimensions["H"].width = 45
    ws.column_dimensions["I"].width = 20
    wb.save(filepath)
    return filepath
