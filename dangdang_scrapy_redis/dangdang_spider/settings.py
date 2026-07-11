"""Scrapy-Redis 配置。

对比普通版新增:
    - SCHEDULER + DUPEFILTER → 全部指向 Redis
    - REDIS_URL 连接字符串
"""

BOT_NAME = "dangdang_redis"
SPIDER_MODULES = ["dangdang_spider.spiders"]

ROBOTSTXT_OBEY = False
DOWNLOAD_DELAY = 1

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
}

# === Redis 分布式配置（关键） ===
# 调度器: Redis 队列（多 worker 共享同一个待爬队列）
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# 去重: Redis 集合（多 worker 共享去重集，不重复爬）
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# Redis 连接（默认 localhost:6379）
REDIS_URL = "redis://127.0.0.1:6379"

# 持久化: 爬完不自动清空 Redis 队列（可断点续爬）
SCHEDULER_PERSIST = True
# 空闲等待: 队列空时等待 5 秒（留时间给其他 worker 推新 URL）
SCHEDULER_IDLE_BEFORE_CLOSE = 5

# Pipeline + Feed 输出
ITEM_PIPELINES = {
    "dangdang_spider.pipelines.CleanPipeline": 100,
    "scrapy_redis.pipelines.RedisPipeline": 200,    # 结果也存 Redis
}

FEEDS = {
    "data/dangdang_redis.csv": {
        "format": "csv", "encoding": "utf-8-sig", "overwrite": True,
        "fields": ["title", "price", "comments", "link"],
    },
}

FEED_EXPORT_ENCODING = "utf-8"
