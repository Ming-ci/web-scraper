"""Redis 种子脚本 — 将起始 URL 推入 Redis 队列。

分布式爬虫的入口：运行此脚本后，所有 worker 自动开始从 Redis 拉取任务。

用法:
    python tools/seed_redis.py                # 推入默认关键词
    python tools/seed_redis.py Java 3         # 自定义关键词和页数
"""

import sys
import redis

REDIS_URL = "redis://127.0.0.1:6379"
QUEUE_KEY = "dangdang:start_urls"


def seed(keyword: str = "Python", pages: int = 3):
    """将搜索关键词的多页 URL 推入 Redis 队列。"""
    r = redis.from_url(REDIS_URL)

    for page in range(1, pages + 1):
        url = f"http://search.dangdang.com/?key={keyword}&act=input&page_index={page}"
        r.lpush(QUEUE_KEY, url)
        print(f"  已推入: {url}")

    count = r.llen(QUEUE_KEY)
    print(f"\nRedis 队列 '{QUEUE_KEY}' 共 {count} 个待爬 URL")


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "Python"
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    print(f"推送关键词 '{keyword}' 的 {pages} 页 URL 到 Redis...\n")
    try:
        seed(keyword, pages)
    except redis.ConnectionError:
        print("\n错误: 无法连接 Redis。请先启动 Redis Server。")
        print("Windows: 下载 https://github.com/tporadowski/redis/releases")
        print("启动: redis-server.exe")
