"""X(Twitter) 推文爬虫 CLI。"""

import argparse
import sys

from twitter.fetcher import from_user
from twitter.storage import to_csv, to_excel


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="X(Twitter) 推文爬虫")
    parser.add_argument("user", help="用户ID（如 ufotable）")
    parser.add_argument("--count", type=int, default=20, help="爬取条数")
    parser.add_argument("--excel", action="store_true", help="导出 Excel")
    args = parser.parse_args()

    print(f"爬取 @{args.user} 的推文（最多 {args.count} 条）...")
    data = from_user(args.user, count=args.count)

    if not data:
        print("未获取到推文，请先登录: python -m twitter.auth")
        sys.exit(1)

    if args.excel:
        path = to_excel(data)
    else:
        path = to_csv(data)

    print(f"共 {len(data)} 条 → {path}")


if __name__ == "__main__":
    main()
