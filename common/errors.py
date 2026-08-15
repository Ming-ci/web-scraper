"""HTTP 状态异常 — 让重试逻辑按类型判断，而非字符串匹配异常消息。"""


class HTTPStatusError(RuntimeError):
    """HTTP 响应非 2xx。

    Attributes:
        status_code: HTTP 状态码（4xx 客户端错误不重试，5xx 服务端错误可重试）
    """

    def __init__(self, status_code: int, message: str = None):
        self.status_code = status_code
        super().__init__(message or f"请求失败，HTTP 状态码：{status_code}")
