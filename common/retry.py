"""请求重试 + 指数退避 —— 网络偶发故障不中断抓取。

端口：
    @retry_on_network_error  — 装饰器，自动重试网络错误

用法：
    from common.retry import retry_on_network_error

    @retry_on_network_error(max_retries=3, base_delay=1.0)
    def fetch(city_code):
        ...
"""

import functools
import random
import sys
import time


def retry_on_network_error(max_retries: int = 3, base_delay: float = 1.0):
    """装饰器：当函数抛出 ConnectionError 或 5xx RuntimeError 时自动重试。

    重试策略：指数退避 + 随机抖动。
        第 1 次重试: ~1.0s  后
        第 2 次重试: ~2.0s  后
        第 3 次重试: ~4.0s  后

    不重试的情况：
        - HTTP 4xx — 客户端错误（重试没用）
        - ValueError — 数据解析错误（重试不会改变页面结构）

    Args:
        max_retries: 最多重试次数，默认 3
        base_delay: 基准等待秒数，首次重试为 base_delay，之后指数翻倍
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ConnectionError as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    delay = base_delay * (2 ** attempt) * random.uniform(0.8, 1.2)
                    print(
                        f"  ⚠ 网络错误，{delay:.1f}s 后重试 (第 {attempt + 1}/{max_retries} 次)...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                except RuntimeError as e:
                    last_exception = e
                    msg = str(e)
                    # 4xx 不重试
                    if "404" in msg or "400" in msg or "403" in msg:
                        raise
                    # 5xx 或其他 HTTP 错误重试
                    if attempt == max_retries:
                        break
                    delay = base_delay * (2 ** attempt) * random.uniform(0.8, 1.2)
                    print(
                        f"  ⚠ HTTP 错误（{msg}），{delay:.1f}s 后重试 (第 {attempt + 1}/{max_retries} 次)...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
