"""中国天气网批量天气抓取 CLI 入口 —— 支持 collect / chart 两个子命令。"""

import argparse
import sys

from weather.scheduler import collect
from weather.chart import draw


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="中国天气网批量天气数据抓取工具"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # collect 子命令
    collect_parser = subparsers.add_parser(
        "collect", help="批量抓取 5 城 7 天预报 → CSV"
    )
    collect_parser.set_defaults(func=lambda _: collect())

    # chart 子命令
    chart_parser = subparsers.add_parser(
        "chart", help="从 CSV 生成温度趋势图"
    )
    chart_parser.set_defaults(func=lambda _: draw())

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
