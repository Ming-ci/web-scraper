"""登录态（Cookie）统一 seam — 一个 jar 表示，多种消费格式。

所有子项目的 cookie 持久化收敛于此：

- **jar**（统一表示）: Playwright `context.cookies()` 格式的完整列表，
  每项含 name/value/domain/path 等 —— 加载时保留完整信息，
  不再出现「加载器丢弃 domain/path、采集器手写拼接」的泄漏。
- **消费格式 adapter**:
    - `flatten_jar()` → {name: value}（curl_cffi / requests 用）
    - `jar_to_playwright()` → Playwright `context.add_cookies()` 就绪格式

持久化文件：`cookies.json`（UTF-8，完整 jar）。
"""

import json
from pathlib import Path


def load_jar(filepath: str | Path) -> list[dict]:
    """从 cookies.json 读取完整 cookie jar（Playwright 格式）。

    Returns:
        cookie jar 列表；文件不存在或损坏返回 []
    """
    path = Path(filepath)
    if not path.exists():
        return []
    try:
        with open(path, encoding="utf-8") as f:
            cookies = json.load(f)
        return cookies if isinstance(cookies, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_jar(filepath: str | Path, cookies: list[dict]) -> None:
    """把 cookie jar 写入 cookies.json（Playwright 格式）。"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cookies, f, ensure_ascii=False, indent=2)


def flatten_jar(jar: list[dict]) -> dict[str, str]:
    """jar → {name: value}（curl_cffi / requests cookies 参数用）。"""
    return {c.get("name", ""): c.get("value", "") for c in jar if c.get("name")}


def jar_to_playwright(jar: list[dict], domain: str = None, path: str = "/") -> list[dict]:
    """jar → Playwright `context.add_cookies()` 就绪格式。

    保留原 jar 中的 domain/path；缺失时用传入的 domain/path 补齐
    （旧文件是扁平 dict 时全部补齐）。

    Args:
        jar: 完整 cookie jar（load_jar 的输出）
        domain: 缺省 domain（如 ".xiaohongshu.com"）
        path: 缺省 path，默认 "/"
    """
    formatted = []
    for c in jar:
        formatted.append({
            "name": c.get("name", ""),
            "value": c.get("value", ""),
            "domain": c.get("domain", domain),
            "path": c.get("path", path),
        })
    return [c for c in formatted if c["name"]]


def has_cookies(filepath: str | Path) -> bool:
    """检查 cookie 文件是否存在且有内容。"""
    return len(load_jar(filepath)) > 0
