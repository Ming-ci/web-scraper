"""当当网商品搜索 Spider。

对比手写版 dangdang/fetcher.py：

手写:  requests.get → encoding='gbk' → BS4 → for循环提取 → 去重 → 返回list
Scrapy: start_requests → parse → yield Item → Pipeline自动去重 → Feed导出

Scrapy 替你做了: 请求调度、GBK解码、去重、CSV输出、重试。
你只需写: 从哪儿开始 + 怎么解析。
"""
import scrapy
from dangdang_spider.items import ProductItem


class DangdangSpider(scrapy.Spider):
    name = "dangdang"                              # 唯一标识，命令行用
    allowed_domains = ["dangdang.com"]              # 防止爬出站
    start_urls = ["http://search.dangdang.com/?key=Python&act=input"]

    # 对比手写版: resp.encoding = 'gbk'
    # Scrapy 自动从 <meta charset> 或 HTTP header 检测编码

    def parse(self, response):
        """解析搜索结果页，产出 ProductItem。

        对比手写版:
          soup.select('ul.bigimg > li')   → for li in lis: 手动构建 dict
          response.css('ul.bigimg > li')  → for li in lis: yield ProductItem
        """
        for li in response.css("ul.bigimg > li"):
            item = ProductItem()

            # 手写: title_el.get('title', '')
            title_el = li.css("p.name > a")
            item["title"] = title_el.attrib.get("title", "") if title_el else ""

            # 手写: price_el.get_text(strip=True)
            price_el = li.css(".search_now_price::text").get()
            item["price"] = price_el.strip() if price_el else ""

            # 手写: comment_el.get_text(strip=True)
            comment_el = li.css(".search_comment_num::text").get()
            item["comments"] = comment_el.strip() if comment_el else ""

            # 手写: link_el.get('href') → '//product...' → 'http://...'
            link_el = li.css("a.pic")
            href = link_el.attrib.get("href", "") if link_el else ""
            item["link"] = response.urljoin(href)      # Scrapy 自动补全 URL!

            yield item

        # === 分页 ===
        # 手写: 手动构造 page_index=2 的 URL 再请求
        # Scrapy: yield Request → 框架自动调度
        current = int(response.css("ul.paging li.active::text").get() or 1)
        next_page = response.urljoin(f"/?key=Python&act=input&page_index={current + 1}")
        if current < 3:      # 只爬 3 页
            yield scrapy.Request(next_page, callback=self.parse)
