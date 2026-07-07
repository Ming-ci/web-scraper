# Scrapy settings for dangdang_spider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "dangdang_spider"

SPIDER_MODULES = ["dangdang_spider.spiders"]
NEWSPIDER_MODULE = "dangdang_spider.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "dangdang_spider (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# 请求延迟 (替代手写 throttle.py)
DOWNLOAD_DELAY = 1

# 浏览器头伪装 (替代手写 headers.py)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
}

# Item Pipeline (替代手写 storage.py)
# 数字越小优先级越高
ITEM_PIPELINES = {
    "dangdang_spider.pipelines.CleanPipeline": 100,   # 先清洗
    "dangdang_spider.pipelines.DedupPipeline": 200,   # 再去重
}

# Feed 导出 — Scrapy 自动输出 CSV/JSON，无需手写 csv.writer!
FEEDS = {
    "data/dangdang_scrapy.csv": {
        "format": "csv",
        "encoding": "utf-8-sig",
        "overwrite": True,
        "fields": ["title", "price", "comments", "link"],
    },
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"
