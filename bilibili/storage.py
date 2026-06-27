"""B站排行榜数据 CSV 持久化。"""

import csv
from pathlib import Path

CSV_COLUMNS = ["title", "author", "plays", "likes", "rank", "category", "scrape_time"]


def save(data: list[dict], filepath: str = "data/bilibili.csv") -> int:
    """排行榜数据写入 CSV，按 (标题, 分区) 去重。

    Returns:
        新增行数
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_keys = set()
    is_new = not path.exists()

    if not is_new:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row.get("title", ""), row.get("category", ""))
                if key[0] and key[1]:
                    existing_keys.add(key)

    new_count = 0
    w_enc = "utf-8-sig" if is_new else "utf-8"
    with open(path, "a", newline="", encoding=w_enc) as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if is_new:
            writer.writeheader()

        for record in data:
            key = (record.get("title", ""), record.get("category", ""))
            if key in existing_keys:
                continue
            row = {col: record.get(col, "") for col in CSV_COLUMNS}
            writer.writerow(row)
            existing_keys.add(key)
            new_count += 1

    return new_count
