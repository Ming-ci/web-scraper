"""请求节奏控制 —— 随机延迟，模拟人类浏览速度，避免被识别为脚本。

端口：
    random_delay(min_s, max_s) — 随机休眠指定区间内的秒数

用法：
    from common.throttle import random_delay
    random_delay(1, 3)    # 随机等 1-3 秒
    random_delay()        # 默认 1.0-2.5 秒
"""

import random
import time


def random_delay(min_seconds: float = 1.0, max_seconds: float = 2.5) -> None:
    """随机休眠一段毫秒级的间隔，模拟人类浏览节奏。

    Args:
        min_seconds: 最短等待秒数，默认 1.0
        max_seconds: 最长等待秒数，默认 2.5
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)
