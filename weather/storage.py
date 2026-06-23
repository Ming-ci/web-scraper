"""CSV 天气数据持久化：合并写入 + (date, city) 覆盖更新。

天气预报每天更新，同一 (date, city) 的新数据应覆盖旧数据，
同时保留未被本次抓取覆盖的历史记录。
"""

import csv
from pathlib import Path

CSV_COLUMNS = [
    "date", "city", "city_code", "weather_desc",
    "temp_high", "temp_low", "humidity", "wind",
]


def _load_all(filepath: str) -> dict[tuple[str, str], dict]:
    """读取 CSV 全部行，返回 {(date, city): row_dict} 索引。"""
    path = Path(filepath)
    if not path.exists():
        return {}

    records = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get("date", ""), row.get("city", ""))
            if key[0] and key[1]:
                records[key] = {col: row.get(col, "") for col in CSV_COLUMNS}
    return records


def _write_all(filepath: str, records: dict[tuple[str, str], dict]) -> None:
    """全量写出 CSV（含 BOM）。"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        # 按日期、城市排序输出，便于阅读
        for key in sorted(records.keys()):
            writer.writerow(records[key])


def save(data: list[dict], filepath: str = "data/weather.csv") -> dict:
    """合并天气数据到 CSV：同 (date, city) 覆盖，其余保留。

    每次抓取 5 城 × 7 天 = 35 条。当新数据中有和已有记录
    相同的 (date, city) 时，用新数据覆盖（预报更新了），
    不在本次抓取范围内的历史记录保持不变。

    Args:
        data: 预报数据列表
        filepath: CSV 文件路径

    Returns:
        {"total": 文件总行数, "new": 新增记录数, "updated": 覆盖更新数}
    """
    existing = _load_all(filepath)
    new_count = 0
    updated_count = 0

    for record in data:
        key = (record.get("date", ""), record.get("city", ""))
        if not key[0] or not key[1]:
            continue
        row = {col: record.get(col, "") for col in CSV_COLUMNS}

        if key in existing:
            updated_count += 1
        else:
            new_count += 1
        existing[key] = row

    _write_all(filepath, existing)

    return {
        "total": len(existing),
        "new": new_count,
        "updated": updated_count,
    }
