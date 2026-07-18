"""YouTube爬虫 CLI。"""
import argparse, sys
from youtube.fetcher import from_file, from_channel
from youtube.storage import to_csv, to_excel

def main():
    if sys.stdout.encoding!="utf-8": sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="YouTube频道视频爬虫")
    sp = p.add_subparsers(dest="mode", help="模式")
    pf = sp.add_parser("file", help="本地HTML")
    pf.add_argument("path"); pf.add_argument("--excel", action="store_true")
    ps = sp.add_parser("search", help="在线爬取(Playwright)")
    ps.add_argument("channel", help="频道ID")
    ps.add_argument("--count", type=int, default=30, help="爬取条数")
    ps.add_argument("--excel", action="store_true")
    args = p.parse_args()

    if args.mode=="file":
        data = from_file(args.path)
    elif args.mode=="search":
        data = from_channel(args.channel, count=args.count)
    else: p.print_help(); sys.exit(0)

    if not data: print("未获取到数据"); sys.exit(1)
    path = to_excel(data) if getattr(args,"excel",False) else to_csv(data)
    print(f"共 {len(data)} 条 → {path}")

if __name__=="__main__": main()
