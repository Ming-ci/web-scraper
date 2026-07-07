"""Item 定义 — Scrapy 的结构化数据容器。对比手写 dict。"""

import scrapy


class ProductItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field()
    comments = scrapy.Field()
    link = scrapy.Field()
