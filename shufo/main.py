"""AI佛书网爬虫 CLI。"""

import argparse
import sys

from shufo.fetcher import from_file, from_search
from shufo.storage import to_csv, to_excel


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="AI佛书网 (shu.fo) 爬虫")
    subparsers = parser.add_subparsers(dest="mode", help="模式")

    p_file = subparsers.add_parser("file", help="从本地 HTML 提取")
    p_file.add_argument("path", help="HTML 文件路径")
    p_file.add_argument("--excel", action="store_true")

    p_search = subparsers.add_parser("search", help="在线爬取（Playwright）")
    p_search.add_argument("--pages", type=int, default=5, help="翻页数（默认 5）")
    p_search.add_argument("--limit", type=int, default=100, help="最多提取条数")
    p_search.add_argument("--excel", action="store_true")

    args = parser.parse_args()

    if args.mode == "file":
        data = from_file(args.path)
    elif args.mode == "search":
        data = from_search(pages=args.pages, limit=args.limit)
    else:
        parser.print_help()
        sys.exit(0)

    if not data:
        print("未获取到数据")
        sys.exit(1)

    if getattr(args, "excel", False):
        path = to_excel(data)
    else:
        path = to_csv(data)

    print(f"共 {len(data)} 条 → {path}")


if __name__ == "__main__":
    main()
