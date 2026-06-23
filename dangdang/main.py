"""当当网商品爬虫 CLI 入口。"""

import argparse
import sys
import time

from dangdang.fetcher import fetch_all
from dangdang.storage import save


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="当当网商品搜索爬虫")
    parser.add_argument(
        "--keyword", default="Python",
        help="搜索关键词（默认: Python）",
    )
    parser.add_argument(
        "--pages", type=int, default=3,
        help="抓取页数（默认: 3，每页 60 条）",
    )
    args = parser.parse_args()

    print(f"搜索关键词：{args.keyword}，共 {args.pages} 页\n")

    start = time.time()
    all_data = fetch_all(args.keyword, args.pages)

    if not all_data:
        print("未获取到任何商品数据。")
        sys.exit(1)

    new_count = save(all_data)
    elapsed = time.time() - start

    print(f"\n完成！抓取 {len(all_data)} 条，新增 {new_count} 条，耗时 {elapsed:.1f}s")
    print(f"数据已保存至 data/dangdang.csv")


if __name__ == "__main__":
    main()
