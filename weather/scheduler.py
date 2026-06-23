"""批量抓取调度：多城市 → china_fetcher → storage → 终端摘要。

接口：
    collect() — 一键抓取 CITY_CODES 中所有城市，追加写入 CSV
"""

import time

from weather.china_fetcher import fetch, CITY_CODES
from weather.storage import save
from common.throttle import random_delay


def collect() -> None:
    """抓取全部城市天气，写入 CSV，打印摘要。

    单城失败不中断其余城市；同一天重复运行时自动跳过已有记录。
    """
    start_time = time.time()
    total_fetched = 0
    failures = 0
    city_list = list(CITY_CODES.items())

    print(f"正在抓取 {len(city_list)} 个城市的天气...\n")

    all_data = []
    for idx, (city_name, code) in enumerate(city_list):
        # 首个城市直接抓，后续城市之间随机延迟 1-3 秒（模拟人类浏览节奏）
        if idx > 0:
            random_delay(1.0, 3.0)

        try:
            data = fetch(code)
            all_data.extend(data)
            total_fetched += len(data)
            print(f"  ○ {city_name} ({code}) — {len(data)} 条")
        except (ConnectionError, RuntimeError, ValueError) as e:
            print(f"  ✗ {city_name} ({code}) 抓取失败：{e}")
            failures += 1
            continue

    # 写入 CSV（合并模式：同日期同城覆盖，其余保留）
    stats = {"total": 0, "new": 0, "updated": 0}
    if all_data:
        stats = save(all_data)

    elapsed = time.time() - start_time

    print()
    print(f"完成！抓取 {total_fetched} 条，新增 {stats['new']} 条，"
          f"更新 {stats['updated']} 条，CSV 共 {stats['total']} 行 "
          f"（{failures} 城失败），耗时 {elapsed:.1f}s")
