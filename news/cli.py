"""新闻自动化流水线 CLI 入口。

工作流: crawl → translate → 用户勾选 → draft
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from news.crawlers.rss_fetcher import crawl, save_raw
from news.ai_engine.translator import translate_all, save_all
from news.ai_engine.drafter import draft


def cmd_crawl() -> None:
    """爬取 RSS → data/raw/"""
    print("正在采集 RSS 新闻...\n")
    items = crawl()
    if not items:
        print("\n未获取到任何新闻。")
        sys.exit(1)

    path = save_raw(items)
    print(f"\n完成！{len(items)} 条新闻已保存至 {path}")


def cmd_translate(args) -> None:
    """翻译标题 → data/candidates/YYYY-MM-DD/"""
    raw_path = args.raw or f"news/data/raw/{datetime.now().strftime('%Y-%m-%d')}.json"

    print(f"正在翻译标题: {raw_path}（最多 {args.limit} 条）\n")
    items = translate_all(raw_path, limit=args.limit)

    if not items:
        print("无翻译结果。")
        sys.exit(0)

    dir_path = save_all(items)
    print(f"\n完成！{len(items)} 条已保存至 {dir_path}")
    print("请打开该目录，在想要做的选题文件中将 [ ] selected 改为 [x] selected")
    print("然后运行: python -m news.cli draft")


def cmd_draft(args) -> None:
    """脚本生成 → data/scripts/"""
    candidates_root = Path("news/data/candidates")
    if args.date:
        candidates_dir = str(candidates_root / args.date)
    else:
        date_dirs = sorted([d for d in candidates_root.iterdir() if d.is_dir()], reverse=True)
        if not date_dirs:
            print("未找到任何候选文件夹。请先运行 translate。")
            sys.exit(0)
        candidates_dir = str(date_dirs[0])
        print(f"扫描最新日期: {date_dirs[0].name}")

    print("正在扫描已标记选题...")
    paths = draft(candidates_dir)

    if not paths:
        print("\n未找到标记为 [x] selected 的选题。")
        print("请在对应文件中将 [ ] selected 改为 [x] selected 后重试。")
        sys.exit(0)

    print(f"\n完成！已生成 {len(paths)} 个脚本文件")


def main() -> None:
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="新闻自动化流水线")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # crawl
    p_crawl = subparsers.add_parser("crawl", help="爬取 RSS 新闻")
    p_crawl.set_defaults(func=lambda _: cmd_crawl())

    # translate
    p_tr = subparsers.add_parser("translate", help="翻译所有新闻标题")
    p_tr.add_argument("--raw", help="raw JSON 路径（默认今天）")
    p_tr.add_argument("--limit", type=int, default=50,
                       help="最多处理条数（默认 50）")
    p_tr.set_defaults(func=cmd_translate)

    # draft
    p_draft = subparsers.add_parser("draft", help="为已标记选题生成脚本")
    p_draft.add_argument("--date", help="指定日期文件夹（默认: 最新）")
    p_draft.set_defaults(func=cmd_draft)

    # run = crawl + translate
    p_run = subparsers.add_parser("run", help="一键 crawl → translate")
    p_run.add_argument("--limit", type=int, default=50)
    p_run.set_defaults(func=lambda args: _run_crawl_then_translate(args))

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


def _run_crawl_then_translate(args) -> None:
    items = crawl()
    if not items:
        print("未获取到任何新闻。")
        sys.exit(1)
    raw_path = save_raw(items)
    print(f"\n{len(items)} 条新闻已保存\n")

    items = translate_all(raw_path, limit=args.limit)
    if items:
        dir_path = save_all(items)
        print(f"\n{len(items)} 条已保存至 {dir_path}")


if __name__ == "__main__":
    main()
