"""CSV + Excel 导出。"""

import csv
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = ["author", "text", "pub_time", "link", "replies",
               "retweets", "likes", "views", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def to_csv(data: list[dict], filepath: str = None) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"twitter_{ts}.csv")
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
        filepath = str(OUTPUT_DIR / f"twitter_{ts}.xlsx")
    wb = Workbook()
    ws = wb.active
    ws.title = "推文"
    headers = ["序号", "用户", "发布内容", "发布时间", "链接",
               "回复", "转发", "点赞", "浏览", "爬取时间"]
    ws.append(headers)
    for i, d in enumerate(data, 1):
        ws.append([i, d.get("author", ""), d.get("text", ""),
                    d.get("pub_time", ""), d.get("link", ""),
                    d.get("replies", ""), d.get("retweets", ""),
                    d.get("likes", ""), d.get("views", ""),
                    d.get("scrape_time", "")])
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 60
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 50
    ws.column_dimensions["F"].width = 8
    ws.column_dimensions["G"].width = 8
    ws.column_dimensions["H"].width = 8
    ws.column_dimensions["I"].width = 8
    ws.column_dimensions["J"].width = 20
    wb.save(filepath)
    return filepath
