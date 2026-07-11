"""结构化日志 — 替代 print()，支持文件轮转 + 控制台同时输出。

用法:
    from common.logger import get_logger
    logger = get_logger(__name__)
    logger.info("开始抓取 %d 条", count)
    logger.warning("第 %d 个源失败: %s", i, err)
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
DEFAULT_FMT = "%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s"
DATE_FMT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup(level: int = logging.INFO, log_file: str = None) -> None:
    """初始化日志系统（只需调用一次）。

    Args:
        level: 日志级别
        log_file: 日志文件路径，默认 logs/app.log
    """
    global _initialized
    if _initialized:
        return

    LOG_DIR.mkdir(exist_ok=True)
    log_file = log_file or str(LOG_DIR / "app.log")

    root = logging.getLogger()
    root.setLevel(level)

    # 控制台 handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(DEFAULT_FMT, DATE_FMT))
    root.addHandler(console)

    # 文件 handler（自动轮转：10MB × 3 个备份）
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(DEFAULT_FMT, DATE_FMT))
    root.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """获取模块级 logger。"""
    if not _initialized:
        setup()
    return logging.getLogger(name)
