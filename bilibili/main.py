"""B站排行榜爬虫 CLI 入口。"""

import argparse
import sys
import time

from bilibili.fetcher import fetch_rank, CATEGORIES
from bilibili.storage import save


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    cat_choices = list(CATEGORIES.keys())
    cat_help = "分区：" + "、".join(f"{k}({v})" for k, v in CATEGORIES.items())

    parser = argparse.ArgumentParser(description="B站排行榜爬虫（Playwright）")
    parser.add_argument(
        "--category", default="tech", choices=cat_choices,
        help=cat_help + "（默认: tech）",
    )
    args = parser.parse_args()

    cat_name = CATEGORIES.get(args.category, args.category)
    print(f"正在抓取 B 站「{cat_name}」排行榜...")

    start = time.time()
    data = fetch_rank(category=args.category)

    if not data:
        print("未获取到任何视频数据。")
        sys.exit(1)

    new_count = save(data)
    elapsed = time.time() - start

    print(f"完成！抓取 {len(data)} 条，新增 {new_count} 条，耗时 {elapsed:.1f}s")
    print(f"数据已保存至 data/bilibili.csv")


if __name__ == "__main__":
    main()
