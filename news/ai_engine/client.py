"""DeepSeek API 客户端 — OpenAI SDK 兼容。

API Key 读取优先级：
    1. 环境变量 DEEPSEEK_API_KEY
    2. 项目配置文件 news/config/api_key.txt（一行纯文本）
"""

import os
from pathlib import Path

from openai import OpenAI

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_key() -> str:
    """从环境变量或配置文件加载 API Key。"""
    # 1. 环境变量
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if key:
        return key

    # 2. 配置文件
    key_file = CONFIG_DIR / "api_key.txt"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    return ""


def _get_client() -> OpenAI:
    api_key = _load_key()
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise RuntimeError(
            "请设置 DEEPSEEK_API_KEY。方式一：写入 news/config/api_key.txt "
            "方式二：设置环境变量 DEEPSEEK_API_KEY"
        )
    return OpenAI(api_key=api_key, base_url=base_url)


def chat(prompt: str, model: str = "deepseek-chat", temperature: float = 0.7,
         max_tokens: int = 2048) -> str:
    """调用 DeepSeek Chat API，返回纯文本回复。"""
    client = _get_client()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()
