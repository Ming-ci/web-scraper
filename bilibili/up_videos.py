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
    """通过 B站公开 API 获取 UP 主投稿视频信息。

    使用 WBI 签名 + TLS 指纹伪装，支持 Cookie 登录态绕过风控。
    """
    from bilibili.wbi import api_request

    all_videos = []
    page = 1

    while len(all_videos) < limit:
        result = api_request("/x/space/wbi/arc/search", {
            "mid": str(mid),
            "ps": "50",
            "pn": str(page),
            "order": "pubdate",
        })

        code = result.get("code", -1)
        if code != 0:
            print(f"API 错误: {result.get('message', '未知')}")
            break

        vlist = result.get("data", {}).get("list", {}).get("vlist", [])
        if not vlist:
            break

        for v in vlist:
            all_videos.append({
                "title": v.get("title", ""),
                "author": v.get("author", ""),
                "mid": str(mid),
                "bvid": v.get("bvid", ""),
                "play": v.get("play", 0),
                "created": datetime.fromtimestamp(v.get("created", 0)).strftime("%Y-%m-%d"),
            })

        if len(vlist) < 50:
            break
        page += 1

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
