"""标题翻译器 — 将所有新闻标题翻译为中文，保存到日期文件夹供用户挑选。"""

import json
from datetime import datetime
from pathlib import Path

import yaml

from news.ai_engine.client import chat

CANDIDATES_DIR = Path(__file__).parent.parent / "data" / "candidates"
PROMPT_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"


def _load_prompts() -> dict:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def translate_all(raw_file: str, limit: int = 50) -> list[dict]:
    """对 raw JSON 中所有新闻标题进行翻译。

    Args:
        raw_file: raw JSON 文件路径
        limit: 最多处理条数

    Returns:
        [{title_en, title_cn, source, link, category}]
    """
    with open(raw_file, encoding="utf-8") as f:
        articles = json.load(f)

    prompts = _load_prompts()
    results = []
    total = min(len(articles), limit)

    # tech 优先
    articles.sort(key=lambda a: 0 if a.get("category") == "tech" else 1)

    for i, article in enumerate(articles[:total]):
        title_en = article["title"]
        source = article["source"]
        link = article.get("link", "")

        if not title_en or not link:
            continue

        print(f"  [{i+1}/{total}] {source}: {title_en[:50]}...", flush=True)

        # 翻译标题
        t_prompt = prompts["title_translate"].format(title=title_en)
        title_cn = chat(t_prompt, temperature=0.3)

        results.append({
            "title_en": title_en,
            "title_cn": title_cn,
            "source": source,
            "link": link,
            "category": article.get("category", ""),
        })

    return results


def save_all(items: list[dict]) -> str:
    """将所有翻译后的标题保存到以日期命名的文件夹。

    格式: data/candidates/YYYY-MM-DD/001-中文标题.md
    每个文件包含原文标题、中文标题、来源、链接、勾选框。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    day_dir = CANDIDATES_DIR / today
    day_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    for i, item in enumerate(items):
        num = str(i + 1).zfill(3)
        slug = item["title_cn"][:40].replace("/", "-").replace(":", "-").replace("?", "").replace("!", "")
        filepath = day_dir / f"{num}-{slug}.md"

        md = f"""# {item['title_cn']}

**来源:** {item['source']}
**分类:** {item.get('category', '-')}
**原文标题:** {item['title_en']}
**原文链接:** {item['link']}
**翻译时间:** {timestamp}

## 状态

[ ] selected — 选定后改为 `[x] selected`

---
*选定后运行 `python -m news.cli draft` 生成脚本。*
"""
        filepath.write_text(md, encoding="utf-8")

    return str(day_dir)
