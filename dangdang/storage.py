"""当当商品数据 CSV 持久化。"""

import csv
from pathlib import Path

CSV_COLUMNS = ["title", "price", "comments", "link"]


def save(data: list[dict], filepath: str = "data/dangdang.csv") -> int:
    """商品数据写入 CSV，追加模式，自动去重（按 link 字段）。

    Args:
        data: 商品列表
        filepath: 输出路径

    Returns:
        实际写入行数
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    # 读取已有链接用于去重
    existing_links = set()
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("link"):
                    existing_links.add(row["link"])

    new_count = 0
    is_new = not path.exists()

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
