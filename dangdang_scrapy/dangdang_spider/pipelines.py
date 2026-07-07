"""Item Pipeline — 替代手写 storage.py 的去重和清洗逻辑。

每条 Item 依次流经所有 Pipeline，按 settings.py 中 ITEM_PIPELINES 的优先级排序。
"""

from scrapy.exceptions import DropItem


class DedupPipeline:
    """按 link 去重 — 替代手写版的 card_links set。"""

    def __init__(self):
        self.seen = set()

    def process_item(self, item, spider):
        link = item.get("link", "")
        if link in self.seen:
            raise DropItem(f"重复: {link}")
        self.seen.add(link)
        return item


class CleanPipeline:
    """清洗字段 — 替代手写版的 strip() 调用。"""

    def process_item(self, item, spider):
        item["title"] = item.get("title", "").strip()
        item["price"] = item.get("price", "").strip()
        item["comments"] = item.get("comments", "").strip()
        item["link"] = item.get("link", "").strip()
        return item
