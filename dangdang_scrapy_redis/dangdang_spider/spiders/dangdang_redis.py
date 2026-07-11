"""当当分布式爬虫 — Scrapy-Redis 版。

对比普通版 (dangdang_scrapy) 的差异只需改 3 处:
    1. 继承 RedisSpider（而非 scrapy.Spider）
    2. redis_key 替代 start_urls（URL 从 Redis 队列取）
    3. 不再手动 yield Request 做分页（所有 URL 推入 Redis 队列）

架构:
    Redis Server (共享队列)
        ↓ pop URL
    Worker-1    Worker-2    Worker-3    ← 多机/多进程，同时从 Redis 拉取
    ↓           ↓           ↓
    各取 URL 解析，产出 Item，回填分页 URL 到 Redis

运行方式:
    1. 先推种子 URL 到 Redis:
       python tools/seed_redis.py

    2. 启动 Workers（多台机器或多终端）:
       cd dangdang_scrapy_redis
       scrapy crawl dangdang_redis
"""
import scrapy
from scrapy_redis.spiders import RedisSpider


class DangdangRedisSpider(RedisSpider):
    name = "dangdang_redis"
    redis_key = "dangdang:start_urls"   # 从 Redis 的该 key pop URL
    allowed_domains = ["dangdang.com"]

    # 分页控制（分布式场景下每个 worker 独立计数无意义，靠 Redis 去重）
    max_depth = 5  # 最多翻 5 页

    def parse(self, response):
        """解析搜索结果页。"""
        for li in response.css("ul.bigimg > li"):
            item = {
                "title": li.css("p.name > a::attr(title)").get("") or "",
                "price": (li.css(".search_now_price::text").get("") or "").strip(),
                "comments": (li.css(".search_comment_num::text").get("") or "").strip(),
                "link": response.urljoin(
                    li.css("a.pic::attr(href)").get("") or ""
                ),
            }
            yield item

        # 分页：把下一页 URL 推入 Redis 队列（而非立即请求）
        current = response.meta.get("depth", 0)
        if current < self.max_depth:
            next_link = response.css("li.next a::attr(href)").get()
            if next_link:
                next_url = response.urljoin(next_link)
                # yield Request → 框架自动入队 Redis
                yield scrapy.Request(next_url, meta={"depth": current + 1})
