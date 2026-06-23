"""从 CSV 读取天气数据，绘制城市温度趋势折线图。

中文字体策略：SimHei → 微软雅黑 → sans-serif fallback
"""

import csv
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# 中文字体探测
_CHINESE_FONT = None
_CANDIDATES = ["SimHei", "Microsoft YaHei", "WenQuanYi Micro Hei", "PingFang SC"]


def _detect_font():
    """探测第一个可用的中文字体，未找到则禁用中文标签。"""
    global _CHINESE_FONT
    if _CHINESE_FONT is not None:
        return _CHINESE_FONT

    from matplotlib.font_manager import FontManager
    fm = FontManager()
    available = {f.name for f in fm.ttflist}

    for name in _CANDIDATES:
        if name in available:
            _CHINESE_FONT = name
            return _CHINESE_FONT

    _CHINESE_FONT = ""  # sentinel: no Chinese font found
    return _CHINESE_FONT


def _setup_style():
    """设置 matplotlib 样式，处理中文显示。"""
    font = _detect_font()
    if font:
        matplotlib.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
        matplotlib.rcParams["axes.unicode_minus"] = False


def _read_csv(csv_path: str) -> dict[str, list[dict]]:
    """读取 CSV，按城市分组返回数据。

    Returns:
        {城市名: [{"date": str, "temp_high": int, "temp_low": int|None, ...}, ...]}
    """
    cities: dict[str, list[dict]] = {}
    path = Path(csv_path)
    if not path.exists():
        print(f"警告：CSV 文件 {csv_path} 不存在，无法生成图表。")
        return cities

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = row.get("city", "")
            if city not in cities:
                cities[city] = []
            try:
                record = {
                    "date": row.get("date", ""),
                    "temp_high": int(row.get("temp_high", 0)) if row.get("temp_high") else None,
                    "temp_low": int(row.get("temp_low", 0)) if row.get("temp_low") else None,
                }
            except (ValueError, TypeError):
                record = {"date": row.get("date", ""), "temp_high": None, "temp_low": None}
            cities[city].append(record)
    return cities


def draw(csv_path: str = "data/weather.csv", output_path: str = "data/trend.png") -> None:
    """从 CSV 读取天气数据，绘制温度趋势折线图并保存为 PNG。

    Args:
        csv_path: CSV 文件路径
        output_path: 输出图片路径
    """
    _setup_style()
    cities_data = _read_csv(csv_path)

    if not cities_data:
        print("没有数据可绘制。请先运行 collect 命令抓取天气数据。")
        return

    # 收集所有日期作为 X 轴（取第一个城市的日期列表）
    all_dates = []
    for records in cities_data.values():
        dates = [r["date"] for r in records]
        if len(dates) > len(all_dates):
            all_dates = dates
    x = list(range(len(all_dates)))

    fig, ax = plt.subplots(figsize=(12, 6))

    for city, records in cities_data.items():
        highs = [r["temp_high"] for r in records]
        lows = [r["temp_low"] for r in records]
        # 对齐：用 records 实际长度对应的 x 位置
        n = len(records)
        x_city = x[:n]

        ax.plot(x_city, highs, marker="o", linewidth=1.5, label=f"{city} 高温")
        # 低温用虚线，如果为 None 则跳过
        if any(l is not None for l in lows):
            valid_lows = [(i, v) for i, v in enumerate(lows) if v is not None]
            if valid_lows:
                lx, ly = zip(*[(x_city[i], v) for i, v in valid_lows])
                ax.plot(lx, ly, marker="s", linestyle="--", linewidth=1.2,
                        label=f"{city} 低温")

    ax.set_xticks(x)
    ax.set_xticklabels(all_dates, rotation=45, ha="right", fontsize=8)
    ax.set_ylabel("温度 (°C)")
    ax.set_title("城市温度趋势图")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))

    # 确保输出目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f"趋势图已保存至 {output_path}")
