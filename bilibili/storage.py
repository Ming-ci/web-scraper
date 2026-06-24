"""B站视频数据 CSV 持久化。"""

import csv
from pathlib import Path

CSV_COLUMNS = ["title", "author", "plays", "likes", "link", "cover"]


def save(data: list[dict], filepath: str = "data/bilibili.csv") -> int:
    """视频数据写入 CSV，按 link 去重。

    Args:
        data: 视频列表
        filepath: 输出路径

    Returns:
        新增行数
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_links = set()
    is_new = not path.exists()

    if not is_new:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("link"):
                    existing_links.add(row["link"])

    new_count = 0
    with open(path, "a", newline="", encoding="utf-8-sig" if is_new else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if is_new:
            writer.writeheader()

        for record in data:
            link = record.get("link", "")
            if link and link in existing_links:
                continue
            row = {col: record.get(col, "") for col in CSV_COLUMNS}
            writer.writerow(row)
            existing_links.add(link)
            new_count += 1

    return new_count
