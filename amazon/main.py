"""亚马逊搜索爬虫 CLI。"""

import argparse
import sys

from amazon.fetcher import from_file
from amazon.storage import to_csv, to_excel


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="亚马逊搜索爬虫")
    parser.add_argument("path", help="本地 HTML 文件路径")
    parser.add_argument("--limit", type=int, help="最多提取条数")
    parser.add_argument("--excel", action="store_true", help="导出 Excel")
    args = parser.parse_args()

    data = from_file(args.path, limit=args.limit)

    if not data:
        print("未获取到数据")
        sys.exit(1)

    if args.excel:
        path = to_excel(data)
    else:
        path = to_csv(data)

    print(f"共 {len(data)} 条 → {path}")


if __name__ == "__main__":
    main()
