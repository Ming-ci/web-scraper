"""请求头伪装 —— 模拟真实浏览器访问，降低被识别为爬虫的概率。

端口：
    get_headers() — 随机返回一组浏览器请求头

用法：
    from common.headers import get_headers
    headers = get_headers()
    resp = requests.get(url, headers=headers, timeout=10)
"""

import random

# 真实浏览器 User-Agent 池（Chrome / Firefox / Edge，Windows 环境）
_USER_AGENTS = [
    # Chrome 126, Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # Firefox 128, Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    # Edge 126, Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
    # Chrome 127, Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    # Firefox 129, Windows 10
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
]

_BASE_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Cache-Control": "no-cache",
    "DNT": "1",  # Do Not Track
    "Upgrade-Insecure-Requests": "1",
}


def get_headers(referer: str = None) -> dict[str, str]:
    """返回一组模拟浏览器的请求头。

    Args:
        referer: 可选，请求来源 URL。不传则默认为 https://www.google.com/

    Returns:
        请求头字典，含随机 User-Agent 和标准浏览器标头
    """
    headers = _BASE_REQUEST_HEADERS.copy()
    headers["User-Agent"] = random.choice(_USER_AGENTS)
    headers["Referer"] = referer or "https://www.google.com/"
    return headers
