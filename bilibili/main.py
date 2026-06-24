"""B站热门视频爬虫 CLI 入口。"""

import argparse
import sys
import time

from bilibili.fetcher import fetch_page
from bilibili.storage import save


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="B站热门视频爬虫（Playwright）")
    parser.add_argument(
        "--scroll", type=int, default=3,
        help="滚动加载次数（默认: 3，约 60 个视频）",
    )
    args = parser.parse_args()

    print(f"正在抓取 B 站热门视频（滚动 {args.scroll} 次）...\n")
    start = time.time()

    data = fetch_page(scroll_times=args.scroll)

    if not data:
        print("未获取到任何视频数据。")
        sys.exit(1)

    new_count = save(data)
    elapsed = time.time() - start

    print(f"完成！抓取 {len(data)} 条，新增 {new_count} 条，耗时 {elapsed:.1f}s")
    print(f"数据已保存至 data/bilibili.csv")


if __name__ == "__main__":
    main()
