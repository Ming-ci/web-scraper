"""淘宝爬虫 CLI。"""
import argparse, sys
from taobao.fetcher import from_file
from taobao.storage import to_csv, to_excel

def main():
    if sys.stdout.encoding != "utf-8": sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="淘宝/天猫搜索爬虫")
    p.add_argument("path", help="本地HTML文件路径")
    p.add_argument("--limit", type=int, help="最多条数")
    p.add_argument("--excel", action="store_true")
    args = p.parse_args()

    data = from_file(args.path, limit=args.limit)
    if not data: print("未提取到商品数据。请确认: 1)已登录 2)搜索结果已加载"); sys.exit(1)

    path = to_excel(data) if args.excel else to_csv(data)
    print(f"共 {len(data)} 条 → {path}")

if __name__ == "__main__": main()
