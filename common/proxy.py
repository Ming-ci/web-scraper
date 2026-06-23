"""IP 代理池 —— 轮换请求 IP，降低被封概率。

端口：
    get_proxies() — 随机返回一组代理配置，用于 requests 的 proxies 参数
    get_proxy_dicts() — 返回所有可用代理的原始列表

配置：
    在项目根目录创建 proxies.json：
    [
        {"http": "http://127.0.0.1:7890",  "https": "http://127.0.0.1:7890"},
        {"http": "http://192.168.1.1:8080", "https": "http://192.168.1.1:8080"}
    ]
    或设置环境变量 HTTP_PROXY / HTTPS_PROXY。

无代理或代理全部不可用时返回 None，调用方走直连。
"""

import json
import os
import random
from pathlib import Path

PROXY_FILE = Path("proxies.json")
ENV_HTTP = ["HTTP_PROXY", "http_proxy"]
ENV_HTTPS = ["HTTPS_PROXY", "https_proxy"]

_proxy_list: list[dict] | None = None  # lazy loaded，None 表示未加载


def _load_from_file() -> list[dict]:
    """从 proxies.json 加载代理列表。"""
    if PROXY_FILE.exists():
        try:
            with open(PROXY_FILE, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _load_from_env() -> dict | None:
    """从环境变量读取代理配置。"""
    http_p = None
    https_p = None
    for var in ENV_HTTP:
        val = os.environ.get(var)
        if val:
            http_p = val
            break
    for var in ENV_HTTPS:
        val = os.environ.get(var)
        if val:
            https_p = val
            break
    if http_p or https_p:
        proxy = {}
        if http_p:
            proxy["http"] = http_p
        if https_p:
            proxy["https"] = https_p
        return proxy
    return None


def _ensure_loaded():
    """懒加载代理列表（文件 + 环境变量）。"""
    global _proxy_list
    if _proxy_list is not None:
        return

    _proxy_list = _load_from_file()
    env_proxy = _load_from_env()
    if env_proxy:
        _proxy_list.append(env_proxy)


def get_proxies() -> dict[str, str] | None:
    """随机返回一组代理配置，可直接传给 requests.get(proxies=...)。

    Returns:
        {"http": "...", "https": "..."} 或 None（无可用代理，走直连）
    """
    _ensure_loaded()
    if not _proxy_list:
        return None
    return random.choice(_proxy_list)


def get_proxy_dicts() -> list[dict]:
    """返回全部可用代理的原始列表（用于调试或展示）。"""
    _ensure_loaded()
    return list(_proxy_list) if _proxy_list else []


def clear_cache():
    """清空缓存的代理列表，强制下次重新加载（代理文件修改后调用）。"""
    global _proxy_list
    _proxy_list = None
