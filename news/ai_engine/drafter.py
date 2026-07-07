"""脚本撰写器 — 对用户选定的选题，抓取全文 → 翻译 → 双版本脚本。

输出 data/scripts/[✓] 标题.md 格式。
"""

import re
from pathlib import Path

import httpx
import trafilatura
import yaml

from news.ai_engine.client import chat

SCRIPTS_DIR = Path(__file__).parent.parent / "data" / "scripts"
PROMPT_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"


def _load_prompts() -> dict:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _fetch_article_text(url: str, timeout: int = 15) -> str:
    """用 httpx + trafilatura 提取网页正文。"""
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; NewsBot/1.0)"})
        if resp.status_code != 200:
            return ""
        text = trafilatura.extract(resp.text, include_comments=False, include_tables=False)
        return text or ""
    except Exception:
        return ""


def draft(candidates_dir: str) -> list[str]:
    """扫描 candidates/ 目录中标记为 [x] selected 的文件，生成双版本脚本。

    Args:
        candidates_dir: candidates/ 目录路径

    Returns:
        生成的脚本文件路径列表
    """
    prompts = _load_prompts()
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    output_paths = []

    candidate_files = sorted(Path(candidates_dir).glob("*.md"))

    for md_file in candidate_files:
        content = md_file.read_text(encoding="utf-8")

        # 检查是否被用户标记（行首以 [x] selected 开头即视为选定）
        selected = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[x] selected") or stripped.startswith("[x]selected"):
                selected = True
                break
        if not selected:
            continue

        print(f"\n{'='*50}")
        print(f"处理: {md_file.name}")

        # 解析 markdown 提取关键信息
        title_cn = _extract_field(content, r"^# (.+)")
        link = _extract_field(content, r"\*\*原文链接:\*\*\s*(.+)")

        if not link:
            print("  ✗ 缺少原文链接，跳过")
            continue

        # 1. 抓取原文
        print(f"  抓取原文: {link[:60]}...")
        article_text = _fetch_article_text(link)
        if not article_text or len(article_text) < 200:
            print("  ✗ 原文抓取失败或太短，跳过")
            continue
        print(f"  原文长度: {len(article_text)} 字符")

        # 2. 全文翻译
        print("  翻译全文...")
        t_prompt = prompts["article_translate"].format(link=link, content=article_text[:8000])
        article_cn = chat(t_prompt, temperature=0.3, max_tokens=4096)

        # 3. 长视频脚本
        print("  生成B站长视频脚本...")
        long_prompt = prompts["script_long"].format(title=title_cn, content=article_cn[:4000])
        script_long = chat(long_prompt, temperature=0.8, max_tokens=4096)

        # 4. 短视频脚本
        print("  生成抖音短视频脚本...")
        short_prompt = prompts["script_short"].format(title=title_cn, content=article_cn[:2000])
        script_short = chat(short_prompt, temperature=0.8, max_tokens=2048)

        # 5. 写出脚本文件
        slug = title_cn[:40].replace("/", "-").replace(":", "-") if title_cn else md_file.stem
        script_content = f"""# {title_cn}

**原文链接:** {link}
**来源:** {_extract_field(content, r'\*\*来源:\*\*\s*(.+)')}

---

## 新闻全文（中文翻译）

{article_cn}

---

## B站长视频脚本（5-10分钟）

{script_long}

---

## 抖音短视频脚本（60-90秒）

{script_short}
"""
        script_file = SCRIPTS_DIR / f"[✓] {slug}.md"
        script_file.write_text(script_content, encoding="utf-8")
        print(f"  ✓ 已生成: {script_file.name}")
        output_paths.append(str(script_file))

    return output_paths


def _extract_field(text: str, pattern: str) -> str:
    """从 Markdown 文本中提取字段值。"""
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1).strip() if match else ""
