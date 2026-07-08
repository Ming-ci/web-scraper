"""TLS 指纹伪装 — curl_cffi 替代 requests，伪装浏览器 TLS 握手。

原理：
    requests 库基于 urllib3，TLS 指纹固定且不同浏览器。
    强反爬站通过 JA3/JA4 指纹在 TLS 握手阶段就识别并拦截脚本。
    curl_cffi 编译了和浏览器一致的 TLS 库，握手特征无法区分。

用法：
    from common.tls import get
    resp = get('https://xxx.com', impersonate='chrome124')

支持的伪装身份: chrome, chrome124, safari17_0, edge101 等。
"""

from curl_cffi import requests as curl_requests


def get(url: str, impersonate: str = "chrome124", timeout: int = 10,
        headers: dict = None, proxies: dict = None) -> curl_requests.Response:
    """发送 GET 请求，伪装为指定浏览器的 TLS 指纹。

    Args:
        url: 请求 URL
        impersonate: 伪装浏览器身份 (chrome/chrome124/safari17_0/edge101...)
        timeout: 超时秒数
        headers: 额外请求头
        proxies: 代理配置

    Returns:
        curl_cffi Response 对象（API 兼容 requests.Response）
    """
    return curl_requests.get(
        url,
        impersonate=impersonate,
        timeout=timeout,
        headers=headers,
        proxies=proxies,
    )
