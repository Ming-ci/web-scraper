"""YouTube InnerTube API 逆向 — 不依赖任何第三方库，直接调用 YouTube 内部接口。

逆向过程:
    1. 首页提取 ytcfg（INNERTUBE_API_KEY + INNERTUBE_CONTEXT）
    2. SAPISID Cookie → SHA1 hash → Authorization 鉴权头
    3. POST youtubei/v1/browse 获取频道视频列表
    4. 递归解析 lockupViewModel → 结构化字段

鉴权公式:
    SAPISIDHASH = "{timestamp}_{sha1(timestamp + SPISID + origin)}"

API 响应格式（YouTube 2026 新版）:
    lockupViewModel > contentImage > thumbnailViewModel > overlays > duration
    lockupViewModel > metadata > lockupMetadataViewModel > title + views + time

参考:
    yt-dlp 源码: youtube.py generate_api_headers() + _call_api()
    YouTube 前端: ytcfg.set() + InnerTube browse endpoint
"""

import json
import re
import hashlib
import time
import random
import string
from datetime import datetime

from curl_cffi import requests as cr


def _get_ytcfg(session, proxy: str) -> dict:
    """从 YouTube 首页提取全局配置。"""
    resp = session.get("https://www.youtube.com", impersonate="chrome124",
                       proxy=proxy, timeout=15)
    m = re.search(r"ytcfg\.set\((\{.*?\})\);", resp.text)
    if not m:
        m = re.search(r"window\.ytcfg\s*=\s*(\{.*?\});", resp.text)
    return json.loads(m.group(1)) if m else {}


def _get_context(ytcfg: dict) -> dict:
    """解析 INNERTUBE_CONTEXT（可能是 JSON 字符串）。"""
    ctx = ytcfg.get("INNERTUBE_CONTEXT", {})
    return json.loads(ctx) if isinstance(ctx, str) else ctx


def _get_sapisid(session) -> str:
    """从 Cookie 中提取 SAPISID，没有则生成随机值。"""
    for c in session.cookies.jar:
        if c.name == "SAPISID":
            return c.value
    sapisid = "".join(random.choices(string.hexdigits.lower(), k=16))
    return sapisid


def _auth_header(sapisid: str) -> str:
    """生成 SAPISIDHASH 鉴权头。"""
    origin = "https://www.youtube.com"
    ts = int(time.time())
    h = hashlib.sha1(f"{ts} {sapisid} {origin}".encode()).hexdigest()
    return f"SAPISIDHASH {ts}_{h}"


def _build_headers(ytcfg: dict, auth: str) -> dict:
    """构造 InnerTube API 请求头。"""
    return {
        "Content-Type": "application/json",
        "X-YouTube-Client-Name": str(ytcfg.get("INNERTUBE_CONTEXT_CLIENT_NAME", "1")),
        "X-YouTube-Client-Version": ytcfg.get("INNERTUBE_CLIENT_VERSION", ""),
        "Origin": "https://www.youtube.com",
        "X-Goog-Visitor-Id": ytcfg.get("VISITOR_DATA", ""),
        "Authorization": auth,
        "User-Agent": _get_context(ytcfg).get("client", {}).get(
            "userAgent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
    }


def _extract_lockups(data: dict, results: list = None) -> list:
    """递归提取所有 lockupViewModel。"""
    if results is None:
        results = []
    if isinstance(data, dict):
        if "lockupViewModel" in data:
            results.append(data["lockupViewModel"])
        for v in data.values():
            _extract_lockups(v, results)
    elif isinstance(data, list):
        for item in data:
            _extract_lockups(item, results)
    return results


def _parse_lockup(lockup: dict, scrape_time: str) -> dict:
    """从 lockupViewModel 提取视频字段。"""
    # 标题: metadata.lockupMetadataViewModel.title.content
    title = ""
    meta = lockup.get("metadata", {}).get("lockupMetadataViewModel", {})
    t = meta.get("title", {})
    if "content" in t:
        title = t["content"]
    elif "runs" in t:
        title = "".join(r.get("text", "") for r in t["runs"])

    # 元数据行: views · time ago
    metadata_text = ""
    for row in meta.get("metadata", {}).get("content", {}).get("rows", []):
        parts = row.get("metadataParts", [])
        for p in parts:
            metadata_text += p.get("text", {}).get("content", "") + " "

    # 时长: overlays > thumbnailBottomOverlayViewModel > badges[0]
    duration = ""
    overlays = lockup.get("contentImage", {}).get("thumbnailViewModel", {}).get("overlays", [])
    for ov in overlays:
        bottom = ov.get("thumbnailBottomOverlayViewModel", {})
        badges = bottom.get("badges", [])
        for b in badges:
            duration = b.get("thumbnailBadgeViewModel", {}).get("text", "")
            if duration:
                break
        if duration:
            break

    # videoId: 从图片 URL 提取
    video_id = ""
    sources = (lockup.get("contentImage", {}).get("thumbnailViewModel", {})
               .get("image", {}).get("sources", []))
    if sources:
        m = re.search(r"/vi/([\w-]+)/", sources[0].get("url", ""))
        if m:
            video_id = m.group(1)

    return {
        "title": title,
        "views": metadata_text.split("·")[-1].strip() if "·" in metadata_text else "",
        "pub_time": metadata_text.split("·")[0].strip() if "·" in metadata_text else metadata_text.strip(),
        "duration": duration,
        "link": f"https://www.youtube.com/watch?v={video_id}" if video_id else "",
        "channel": "",  # lockupViewModel 不含频道名
        "scrape_time": scrape_time,
    }


def browse_channel(channel_handle: str, count: int = 30, proxy: str = None) -> list[dict]:
    """纯 Python 逆向：调 InnerTube API 获取频道视频。

    不使用 yt-dlp，完整还原 YouTube 前端 API 调用链路。

    Args:
        channel_handle: @用户名 或 UCxxx 频道 ID
        count: 爬取条数
        proxy: HTTP 代理

    Returns:
        视频数据列表
    """
    proxy = proxy or "http://127.0.0.1:7890"
    scrape_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = cr.Session()

    # 1. 获取配置
    ytcfg = _get_ytcfg(session, proxy)
    if not ytcfg:
        return []

    # 2. UC ID
    if not channel_handle.startswith("UC"):
        url = f"https://www.youtube.com/@{channel_handle}/videos"
        resp = session.get(url, impersonate="chrome124", proxy=proxy, timeout=15)
        m = re.search(r'"externalId":"(UC[\w-]+)"', resp.text)
        if m:
            channel_handle = m.group(1)
        else:
            return []

    # 3. 鉴权
    auth = _auth_header(_get_sapisid(session))
    headers = _build_headers(ytcfg, auth)
    inner_ctx = _get_context(ytcfg)

    # 4. 调 API
    body = {"context": inner_ctx, "browseId": channel_handle}
    api_key = ytcfg.get("INNERTUBE_API_KEY", "")
    resp = session.post(
        f"https://www.youtube.com/youtubei/v1/browse?key={api_key}",
        json=body, headers=headers, impersonate="chrome124", proxy=proxy, timeout=15,
    )
    data = resp.json()
    if data.get("error"):
        return []

    # 5. 解析
    lockups = _extract_lockups(data)
    results = []
    seen = set()
    for lockup in lockups:
        parsed = _parse_lockup(lockup, scrape_time)
        if parsed["link"] and parsed["link"] not in seen:
            seen.add(parsed["link"])
            results.append(parsed)

    return results[:count]
