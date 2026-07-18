"""CSV + Excel 导出。"""
import csv
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = ["title", "views", "pub_time", "duration", "link", "channel", "scrape_time"]
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def to_csv(data: list[dict], filepath: str = None) -> str:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if filepath is None:
        filepath = str(OUTPUT_DIR / f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
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
        filepath = str(OUTPUT_DIR / f"youtube_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "视频"
    ws.append(["序号","标题","播放量","发布时间","时长","链接","频道","爬取时间"])
    for i, d in enumerate(data,1):
        ws.append([i,d.get("title",""),d.get("views",""),d.get("pub_time",""),
                    d.get("duration",""),d.get("link",""),d.get("channel",""),
                    d.get("scrape_time","")])
    ws.column_dimensions["A"].width=6; ws.column_dimensions["B"].width=60
    ws.column_dimensions["C"].width=12; ws.column_dimensions["D"].width=10
    ws.column_dimensions["E"].width=8; ws.column_dimensions["F"].width=50
    ws.column_dimensions["G"].width=20; ws.column_dimensions["H"].width=20
    wb.save(filepath)
    return filepath
