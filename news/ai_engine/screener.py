"""选题筛选器 — AI 标题翻译 + 评分筛选。

流程：
    1. 读 raw JSON → 遍历每条新闻
    2. 调 AI 翻译标题
    3. 调 AI 评分/筛选
    4. 输出 candidates/ 目录的 Markdown 文件
"""

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


def screen(raw_file: str, limit: int = 30) -> list[dict]:
    """对 raw JSON 中的新闻进行标题翻译 + AI 筛选。

    Args:
        raw_file: raw JSON 文件路径
        limit: 最多处理条数（控制 API 消耗）

    Returns:
        候选列表 [{title_cn, score, fun_factor, newsworthiness, angle, why, verdict, link, source}]
    """
    with open(raw_file, encoding="utf-8") as f:
        articles = json.load(f)

    prompts = _load_prompts()
    candidates = []
    total = min(len(articles), limit)

    # 按 tech 优先排序（tech 类先处理）
    articles.sort(key=lambda a: 0 if a.get("category") == "tech" else 1)

    for i, article in enumerate(articles[:total]):
        title_en = article["title"]
        source = article["source"]
        link = article["link"]

        if not title_en or not link:
            continue

        print(f"  [{i+1}/{total}] {source}: {title_en[:50]}...", flush=True)

        # 步骤1：标题翻译
        t_prompt = prompts["title_translate"].format(title=title_en)
        title_cn = chat(t_prompt, temperature=0.3)

        # 步骤2：选题筛选
        s_prompt = prompts["screen"].format(
            title=title_cn, source=source, link=link
        )
        try:
            result_json = chat(s_prompt, temperature=0.3)
            # 尝试解析 JSON
            result = json.loads(result_json)
        except json.JSONDecodeError:
            # AI 可能返回非标准 JSON，尝试提取
            import re
            match = re.search(r'\{[^}]+\}', result_json, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group())
                except json.JSONDecodeError:
                    result = {"verdict": "skip", "fun_score": 0}
            else:
                result = {"verdict": "skip", "fun_score": 0}

        candidates.append({
            "title_en": title_en,
            "title_cn": title_cn,
            "source": source,
            "link": link,
            "fun_score": result.get("fun_score", 0),
            "relevance_score": result.get("relevance_score", 0),
            "roast_score": result.get("roast_score", 0),
            "angle": result.get("angle", ""),
            "why": result.get("why", ""),
            "verdict": result.get("verdict", "skip"),
        })

        # 只显示 pick 的
        if result.get("verdict") == "pick":
            f = result.get('fun_score', 0)
            r = result.get('relevance_score', 0)
            ro = result.get('roast_score', 0)
            print(f"    → PICK 有趣:{f}/5 大众:{r}/5 吐槽:{ro}/5 {title_cn[:50]}")

    return candidates


def save_candidates(candidates: list[dict]) -> str:
    """保存候选选题为 Markdown 文件，返回目录路径。

    格式：data/candidates/001-新闻标题.md
    文件名含数字编号，做过的用 [✓] 标记。
    """
    today = datetime.now().strftime("%Y-%m-%d")
    day_dir = CANDIDATES_DIR / today
    day_dir.mkdir(parents=True, exist_ok=True)

    picks = [c for c in candidates if c["verdict"] == "pick"]
    picks.sort(key=lambda c: c.get("fun_score", 0) + c.get("roast_score", 0), reverse=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    for i, candidate in enumerate(picks):
        num = str(i + 1).zfill(3)
        slug = candidate["title_cn"][:40].replace("/", "-").replace(":", "-")
        filename = f"{num}-{slug}.md"
        filepath = day_dir / filename

        f = candidate.get('fun_score', 0)
        r = candidate.get('relevance_score', 0)
        ro = candidate.get('roast_score', 0)

        md = f"""# {candidate['title_cn']}

**来源:** {candidate['source']}
**原文链接:** {candidate['link']}
**原文标题:** {candidate['title_en']}
**评分:** 有趣:{f}/5 | 大众:{r}/5 | 吐槽:{ro}/5
**筛选时间:** {timestamp}

## 为什么做这个选题

{candidate['why']}

## 建议切入角度

{candidate['angle']}

## 状态

[ ] selected — 选定后将此行改为 `[x] selected`

---
*选定后运行 `python -m news.cli draft` 生成脚本。*
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md)

    return str(day_dir)
