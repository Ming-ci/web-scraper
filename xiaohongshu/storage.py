"""CSV + Excel 导出。"""

import csv
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = ["title", "author", "pub_time", "likes", "link", "cover", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def to_csv(data: list[dict], filepath: str = None) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"xiaohongshu_{ts}.csv")

    seen = set()
    new_count = 0
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for d in data:
            link = d.get("link", "")
            if link and link not in seen:
                seen.add(link)
                writer.writerow({k: d.get(k, "") for k in CSV_COLUMNS})
                new_count += 1
    return filepath


def to_excel(data: list[dict], filepath: str = None) -> str:
    from openpyxl import Workbook

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"xiaohongshu_{ts}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "搜索结果"
    ws.append(["序号", "标题", "博主", "发布时间", "点赞数", "链接", "封面图", "抓取时间"])

    for i, d in enumerate(data, 1):
        ws.append([i, d.get("title", ""), d.get("author", ""),
                    d.get("pub_time", ""), d.get("likes", ""),
                    d.get("link", ""), d.get("cover", ""),
                    d.get("scrape_time", "")])

    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 55
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 40
    ws.column_dimensions["G"].width = 45
    ws.column_dimensions["H"].width = 20

    wb.save(filepath)
    return filepath
