"""通用存储 — CSV / Excel 导出深模块。

所有子项目的 storage 收敛于此：写入编码（utf-8-sig）、序号列、列宽、
追加去重、合并覆盖等逻辑只有一个实现。子项目只声明自己的列定义与
默认输出目录（薄 adapter）。

接口速览：
    to_csv(data, columns, filepath, dedup_key=None, numbered=False)
        — 覆盖写 CSV；dedup_key 去重；numbered 加「序号」首列
    to_excel(data, columns, headers, filepath, sheet_title, col_widths=None)
        — 覆盖写 Excel，自动加「序号」首列
    append_csv(data, columns, filepath, dedup_key=None)
        — 追加写 CSV（自动去重），返回新增行数
    merge_csv(data, columns, filepath, key_cols)
        — 合并写 CSV：同 key 覆盖更新，其余保留；返回 {total,new,updated}
"""

import csv
from pathlib import Path


def _ensure_parent(filepath: str) -> None:
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)


def to_csv(data: list[dict], columns: list[str], filepath: str,
           dedup_key: str = None, numbered: bool = False) -> str:
    """覆盖写 CSV（utf-8-sig 含 BOM）。

    Args:
        data: 记录列表
        columns: 列定义（输出顺序）
        filepath: 输出路径
        dedup_key: 按该字段去重（空串跳过）
        numbered: 加「序号」首列
    """
    _ensure_parent(filepath)
    seen = set()
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["序号"] + columns if numbered else columns)
        for i, d in enumerate(data, 1):
            if dedup_key:
                key = d.get(dedup_key, "")
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
            row = [d.get(k, "") for k in columns]
            writer.writerow([i] + row if numbered else row)
    return filepath


def to_excel(data: list[dict], columns: list[str], headers: list[str],
             filepath: str, sheet_title: str = "数据",
             col_widths: dict = None) -> str:
    """覆盖写 Excel（xlsx）。

    Args:
        data: 记录列表
        columns: 列定义（与 headers 一一对应）
        headers: 中文表头（不含「序号」）
        filepath: 输出路径
        sheet_title: 工作表名
        col_widths: {列字母: 宽度}，如 {"A": 6, "B": 55}
    """
    from openpyxl import Workbook

    _ensure_parent(filepath)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(["序号"] + headers)
    for i, d in enumerate(data, 1):
        ws.append([i] + [d.get(k, "") for k in columns])
    for col, width in (col_widths or {}).items():
        ws.column_dimensions[col].width = width
    wb.save(filepath)
    return filepath


def append_csv(data: list[dict], columns: list[str], filepath: str,
               dedup_key: str = None, dedup_keys: list[str] = None) -> int:
    """追加写 CSV，自动去重（按 dedup_key 或 dedup_keys 复合键；新文件写表头）。

    Args:
        data: 记录列表
        columns: 列定义
        filepath: 输出路径
        dedup_key: 单字段去重键（可选）
        dedup_keys: 多字段复合去重键（可选，优先于 dedup_key）

    Returns:
        新增行数
    """
    key_cols = dedup_keys or ([dedup_key] if dedup_key else [])
    _ensure_parent(filepath)
    path = Path(filepath)
    is_new = not path.exists()

    existing_keys = set()
    if not is_new:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = tuple(row.get(c, "") for c in key_cols) if key_cols else ()
                if any(key):
                    existing_keys.add(key)

    new_count = 0
    with open(path, "a", newline="", encoding="utf-8-sig" if is_new else "utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        if is_new:
            writer.writeheader()
        for record in data:
            key = tuple(record.get(c, "") for c in key_cols) if key_cols else ()
            if key_cols and key in existing_keys:
                continue
            writer.writerow({col: record.get(col, "") for col in columns})
            if key_cols:
                existing_keys.add(key)
            new_count += 1
    return new_count


def merge_csv(data: list[dict], columns: list[str], filepath: str,
              key_cols: list[str]) -> dict:
    """合并写 CSV：同 (key_cols) 覆盖更新，其余保留。

    Args:
        data: 记录列表
        columns: 列定义
        filepath: 输出路径
        key_cols: 合并键字段（如 ["date", "city"]）

    Returns:
        {"total": 文件总行数, "new": 新增记录数, "updated": 覆盖更新数}
    """
    _ensure_parent(filepath)
    path = Path(filepath)

    def _key(row: dict) -> tuple:
        return tuple(row.get(c, "") for c in key_cols)

    records = {}
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                key = _key(row)
                if all(key):
                    records[key] = {col: row.get(col, "") for col in columns}

    new_count = 0
    updated_count = 0
    for record in data:
        key = _key(record)
        if not all(key):
            continue
        if key in records:
            updated_count += 1
        else:
            new_count += 1
        records[key] = {col: record.get(col, "") for col in columns}

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for key in sorted(records.keys()):
            writer.writerow(records[key])

    return {"total": len(records), "new": new_count, "updated": updated_count}
