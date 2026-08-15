"""天气数据 CSV 持久化（薄 adapter，逻辑在 common.storage）。

合并写入 + (date, city) 覆盖更新：天气预报每天更新，同一 (date, city)
的新数据应覆盖旧数据，同时保留未被本次抓取覆盖的历史记录。
"""
from common.storage import merge_csv

CSV_COLUMNS = [
    "date", "city", "city_code", "weather_desc",
    "temp_high", "temp_low", "humidity", "wind",
]


def save(data: list[dict], filepath: str = "data/weather.csv") -> dict:
    """合并天气数据到 CSV：同 (date, city) 覆盖，其余保留。

    Args:
        data: 预报数据列表
        filepath: CSV 文件路径

    Returns:
        {"total": 文件总行数, "new": 新增记录数, "updated": 覆盖更新数}
    """
    return merge_csv(data, CSV_COLUMNS, filepath, key_cols=["date", "city"])
