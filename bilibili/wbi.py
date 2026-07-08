"""B站 WBI 签名 — 调用需要认证的公开 API。

WBI 签名流程:
    1. 从 /x/web-interface/nav 获取 img_key 和 sub_key
    2. 混合 → 拼接 → 取前 32 字符作为实际签名密钥
    3. 请求参数按 key 排序 → 拼接 → 附加 wts(时间戳)
    4. MD5(params + key) → w_rid

文档: https://github.com/SocialSisterYi/bilibili-API-collect
"""

import hashlib
import time
import urllib.parse
from functools import lru_cache

from curl_cffi import requests as curl_requests

MIXIN_TABLE = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 52, 44, 34,
]


@lru_cache(maxsize=1)
def _get_signing_key() -> str:
    """从 B站导航接口获取并计算签名密钥（缓存 1 小时）。"""
    resp = curl_requests.get(
        "https://api.bilibili.com/x/web-interface/nav",
        headers={"User-Agent": "Mozilla/5.0"},
        impersonate="chrome124",
        timeout=10,
    )
    data = resp.json()["data"]
    # 新版 API: key 嵌入在 URL 文件名中
    img_key = data["wbi_img"]["img_url"].split("/")[-1].replace(".png", "")
    sub_key = data["wbi_img"]["sub_url"].split("/")[-1].replace(".png", "")

    # 拼接 → 按映射表重排 → 取前 32 字符
    combined = img_key + sub_key
    result = "".join(combined[i] for i in MIXIN_TABLE if i < len(combined))
    return result[:32]


def sign_params(params: dict) -> dict:
    """给请求参数字典加上 WBI 签名（w_rid + wts）。

    Args:
        params: 原始请求参数字典（不含 w_rid 和 wts）

    Returns:
        签名后的参数字典
    """
    key = _get_signing_key()
    # 排序
    sorted_params = dict(sorted(params.items()))
    # 加时间戳
    sorted_params["wts"] = int(time.time())
    # 拼接 URL 查询字符串
    query = urllib.parse.urlencode(sorted_params)
    # MD5 签名
    w_rid = hashlib.md5((query + key).encode()).hexdigest()
    sorted_params["w_rid"] = w_rid
    return sorted_params


def api_request(endpoint: str, params: dict) -> dict:
    """向 B站 API 发送签名后的 GET 请求。

    Args:
        endpoint: API 路径，如 "/x/space/wbi/arc/search"
        params: 业务参数字典

    Returns:
        API 返回的 JSON dict
    """
    signed = sign_params(params)

    # 尝试加载登录态 Cookie（绕过风控）
    cookies = {}
    try:
        from bilibili.auth import load_cookies
        cookies = load_cookies()
    except ImportError:
        pass

    resp = curl_requests.get(
        f"https://api.bilibili.com{endpoint}",
        params=signed,
        cookies=cookies or None,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bilibili.com/",
        },
        impersonate="chrome124",
        timeout=10,
    )
    return resp.json()
