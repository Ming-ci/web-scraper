"""Session 管理 —— 用 requests.Session 维持 Cookie 和连接复用。

端口：
    create_session()  — 创建已配置好浏览器 headers 的 Session
    save_cookies()    — 将当前 Cookie 持久化到文件（JSON jar，见 common.auth）
    load_cookies()    — 从文件恢复 Cookie（跨启动保持登录态）

原理：
    requests.get()          → 无状态请求，每次独立
    session.get()           → 有状态请求，自动存储/发送 Cookie
    save/load_cookies()     → Cookie 落盘，脚本重启后仍保持登录态
"""

from pathlib import Path

import requests

from common.auth import load_jar, save_jar
from common.headers import get_headers

DEFAULT_COOKIE_FILE = Path("cookies.json")


def create_session() -> requests.Session:
    """创建预配置了浏览器 headers 的 Session 实例。

    该 Session 会自动：
    - 为每个请求携带浏览器 User-Agent（通过 session.headers）
    - 接收并存储服务器返回的 Set-Cookie
    - 复用 TCP 连接（connection pooling）

    Returns:
        已配置的 requests.Session 实例
    """
    session = requests.Session()
    session.headers.update(get_headers())
    return session


def _jar_from_session(session: requests.Session) -> list[dict]:
    """把 requests CookieJar 转为 JSON jar（Playwright 兼容格式）。"""
    jar = []
    for c in session.cookies:
        jar.append({
            "name": c.name,
            "value": c.value,
            "domain": c.domain or "",
            "path": c.path or "/",
        })
    return jar


def save_cookies(session: requests.Session, path: str = None) -> None:
    """将 Session 中的 Cookie 序列化到文件（JSON jar 格式）。

    Args:
        session: 发起过请求的 Session（已设置了 Cookie）
        path: 保存路径，默认 cookies.json
    """
    filepath = Path(path) if path else DEFAULT_COOKIE_FILE
    save_jar(filepath, _jar_from_session(session))


def load_cookies(session: requests.Session, path: str = None) -> bool:
    """从文件恢复 Cookie 到 Session（JSON jar 格式）。

    Args:
        session: 待恢复的 Session
        path: Cookie 文件路径，默认 cookies.json

    Returns:
        True 表示成功加载，False 表示文件不存在或损坏
    """
    filepath = Path(path) if path else DEFAULT_COOKIE_FILE
    jar = load_jar(filepath)
    if not jar:
        return False
    for c in jar:
        session.cookies.set(
            c.get("name", ""),
            c.get("value", ""),
            domain=c.get("domain") or None,
            path=c.get("path") or "/",
        )
    return True
