"""亚马逊搜索爬虫 CLI。"""

import argparse
import sys

from amazon.fetcher import from_file, from_search
from amazon.storage import to_csv, to_excel


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="亚马逊搜索爬虫")
    subparsers = parser.add_subparsers(dest="mode", help="模式")

    p_file = subparsers.add_parser("file", help="从本地 HTML 提取")
    p_file.add_argument("path", help="HTML 文件路径")
    p_file.add_argument("--limit", type=int, help="最多提取条数")
    p_file.add_argument("--excel", action="store_true", help="导出 Excel")

    p_search = subparsers.add_parser("search", help="在线搜索（curl_cffi）")
    p_search.add_argument("--keyword", default="Nike", help="搜索关键词")
    p_search.add_argument("--limit", type=int, help="最多提取条数")
    p_search.add_argument("--excel", action="store_true", help="导出 Excel")

    args = parser.parse_args()

    if args.mode == "file":
        data = from_file(args.path, limit=args.limit)
    elif args.mode == "search":
        data = from_search(args.keyword, limit=args.limit)
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
