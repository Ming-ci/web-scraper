"""当当商品数据 CSV 持久化（薄 adapter，逻辑在 common.storage）。"""
from common.storage import append_csv

CSV_COLUMNS = ["title", "price", "comments", "link"]


def save(data: list[dict], filepath: str = "data/dangdang.csv") -> int:
    """商品数据追加写入 CSV，自动去重（按 link 字段）。

    Args:
        data: 商品列表
        filepath: 输出路径

    Returns:
        实际写入行数
    """
    return append_csv(data, CSV_COLUMNS, filepath, dedup_key="link")
