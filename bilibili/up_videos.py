"""提取 B站 UP 主投稿视频信息，支持终端显示 + Excel 导出。

用法:
    python -m bilibili.up_videos --mid 17076171 30          # 终端打印
    python -m bilibili.up_videos --mid 17076171 30 --excel  # 导出 Excel
    python -m bilibili.up_videos --file data/xxx.html       # 本地 HTML
"""

import sys
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

OUTPUT_DIR = Path(__file__).parent.parent / "data"


def from_file(filepath: str, limit: int = None) -> list[dict]:
    """从本地 HTML 文件提取视频信息。"""
    with open(filepath, encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    titles = soup.select("div.bili-video-card__title")
    results = []
    for t in titles:
        text = t.get_text(strip=True)
        if text:
            results.append({"title": text, "author": "", "mid": ""})
    if limit:
        results = results[:limit]
    return results


def from_up_id(mid: str, limit: int = 30) -> list[dict]:
    """通过 B站公开 API 获取 UP 主投稿视频信息（多线程）。

    先请求第 1 页确定总数 → 计算总页数 → 并发拉取剩余页。
    使用 WBI 签名 + TLS 指纹伪装，支持 Cookie 登录态绕过风控。
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from bilibili.wbi import api_request

    def _parse_vlist(vlist: list) -> list[dict]:
        """将 API 返回的 vlist 转为结构化 dict。"""
        return [{
            "title": v.get("title", ""),
            "author": v.get("author", ""),
            "mid": str(mid),
            "bvid": v.get("bvid", ""),
            "play": v.get("play", 0),
            "created": datetime.fromtimestamp(v.get("created", 0)).strftime("%Y-%m-%d"),
        } for v in vlist]

    def _fetch_page(pn: int) -> tuple[int, list[dict]]:
        """抓取单页，返回 (页码, 视频列表)。"""
        result = api_request("/x/space/wbi/arc/search", {
            "mid": str(mid), "ps": "50", "pn": str(pn), "order": "pubdate",
        })
        vlist = result.get("data", {}).get("list", {}).get("vlist", [])
        return (pn, _parse_vlist(vlist))

    # 1. 先请求第 1 页，确定总数
    print(f"  第 1 页...", end=" ", flush=True)
    p1_result = api_request("/x/space/wbi/arc/search", {
        "mid": str(mid), "ps": "50", "pn": "1", "order": "pubdate",
    })
    p1_vlist = p1_result.get("data", {}).get("list", {}).get("vlist", [])
    all_videos = _parse_vlist(p1_vlist)
    print(f"{len(p1_vlist)} 条")

    # 计算总页数
    total = p1_result.get("data", {}).get("page", {}).get("count", 0)
    total_pages = min((total + 49) // 50, (limit + 49) // 50)
    if total_pages <= 1:
        return all_videos[:limit]

    # 2. 并发拉取剩余页
    remaining = list(range(2, total_pages + 1))
    workers = min(4, len(remaining))  # 最多 4 线程
    print(f"  并发拉取第 2-{total_pages} 页（{workers} 线程）...", end=" ", flush=True)

    results_by_page = {1: all_videos}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_fetch_page, pn): pn for pn in remaining}
        for future in as_completed(futures):
            pn, vlist = future.result()
            results_by_page[pn] = vlist

    # 3. 按页码合并
    for pn in sorted(results_by_page):
        if pn > 1:
            all_videos.extend(results_by_page[pn])

    print(f"共 {len(all_videos)} 条")
    return all_videos[:limit]


def to_excel(videos: list[dict], filepath: str = None) -> str:
    """导出视频列表为 Excel 文件。"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = "视频列表"

    # 表头
    headers = ["序号", "标题", "UP主", "MID", "BV号", "播放量", "发布日期"]
    ws.append(headers)

    for i, v in enumerate(videos, 1):
        ws.append([
            i,
            v.get("title", ""),
            v.get("author", ""),
            v.get("mid", ""),
            v.get("bvid", ""),
            v.get("play", 0),
            v.get("created", ""),
        ])

    # 调整列宽
    ws.column_dimensions["A"].width = 6
    ws.column_dimensions["B"].width = 60
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 14
    ws.column_dimensions["E"].width = 16
    ws.column_dimensions["F"].width = 10
    ws.column_dimensions["G"].width = 14

    if filepath is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = str(OUTPUT_DIR / f"bilibili_videos_{ts}.xlsx")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wb.save(filepath)
    return filepath


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python -m bilibili.up_videos --mid 12345678 30")
        print("  python -m bilibili.up_videos --mid 12345678 30 --excel")
        print("  python -m bilibili.up_videos --file data/xxx.html")
        sys.exit(1)

    mode = sys.argv[1]
    excel = "--excel" in sys.argv
    args = [a for a in sys.argv if a != "--excel"]

    if mode == "--file":
        path = args[2] if len(args) > 2 else None
        if not path:
            print("请提供文件路径")
            sys.exit(1)
        limit = int(args[3]) if len(args) > 3 else None
        videos = from_file(path, limit=limit)
    elif mode == "--mid":
        mid = args[2] if len(args) > 2 else None
        if not mid:
            print("请提供 UP 主 mid 号")
            sys.exit(1)
        limit = int(args[3]) if len(args) > 3 else 30
        videos = from_up_id(mid, limit=limit)
    else:
        print("未知参数，使用 --mid 或 --file")
        sys.exit(1)

    if not videos:
        print("未获取到任何视频数据。")
        sys.exit(1)

    if excel:
        path = to_excel(videos)
        print(f"已导出 {len(videos)} 条到 {path}")
    else:
        print(f"共 {len(videos)} 个视频\n")
        for i, v in enumerate(videos, 1):
            print(f"{i:3d}. [{v['play']:>6}播放] {v['title'][:60]}")
