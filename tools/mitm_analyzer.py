"""mitmproxy 内联脚本 — 自动记录捕获到的 API 请求。

用法:
    1. 启动 mitmweb 并加载此脚本:
       mitmweb -s tools/mitm_analyzer.py

    2. 配置系统代理: 127.0.0.1:8080
       或手机 WiFi 代理指向本机 IP:8080

    3. 访问目标 App/网页 → 所有 API 请求自动记录到 data/api_log.json

输出: data/api_log.json — 含 URL、method、headers、body、response 摘要
"""

import json
from datetime import datetime
from pathlib import Path

from mitmproxy import http

LOG_FILE = Path("data/api_log.json")


def _append(entry: dict):
    existing = []
    if LOG_FILE.exists():
        try:
            existing = json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    existing.append(entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")


def request(flow: http.HTTPFlow) -> None:
    url = flow.request.pretty_url
    if any(kw in url for kw in ["/api/", "/x/", "json", "graphql"]):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": flow.request.method,
            "url": url,
            "headers": dict(flow.request.headers),
            "body": flow.request.get_text()[:2000],
        }
        _append(entry)


def response(flow: http.HTTPFlow) -> None:
    url = flow.request.pretty_url
    if any(kw in url for kw in ["/api/", "/x/", "json"]):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "method": flow.request.method,
            "url": url,
            "status": flow.response.status_code,
            "response_preview": flow.response.get_text()[:500],
        }
        _append(entry)
