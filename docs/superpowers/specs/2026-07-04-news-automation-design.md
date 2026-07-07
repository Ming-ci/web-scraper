# 新闻自动化流水线 — 设计文档

**日期:** 2026-07-04  
**状态:** 设计完成，等待审核

---

## 项目概述

通过自动化爬虫收集海外新闻，AI 筛选出有趣/值得挖掘的选题并生成视频脚本初稿，人工审阅润色后，手动制作视频发布到 B站（长视频深度版）和抖音（短视频吐槽版）。

**目标：** 单人操作、2-3 天一期、半自动化效率最大化。

---

## 一、技术选型

| 层 | 技术 | 依赖 |
|------|------|------|
| 爬虫 | feedparser + httpx | `feedparser`, `httpx` |
| 正文提取 | trafilatura | `trafilatura` |
| AI 翻译/筛选/写稿 | DeepSeek API (OpenAI SDK 兼容) | `openai` |
| 信息图 | Pillow | `Pillow` |
| 配置管理 | YAML | `pyyaml` |
| 定时任务 | Windows 任务计划程序 / `schedule` | `schedule` |
| 语言 | Python 3.11+ | — |

**架构模式：** 模块化管道。5 层独立模块通过数据库(SQLite) + 文件系统解耦。

---

## 二、架构与数据流

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐
│ 爬虫层   │→│ 处理层    │→│ AI层     │→│ 人工审核站    │
│ RSS 采集 │  │ 去重      │  │ 翻译     │  │ 翻 Markdown   │
│ 原文抓取 │  │ 分类      │  │ 筛选打分 │  │ 审阅选题      │
│          │  │ 清洗      │  │ 写稿     │  │ 勾选要做的    │
│          │  │          │  │ 素材建议 │  │ 改文案        │
└──────────┘  └──────────┘  └──────────┘  └──────┬───────┘
                                                  │
                                          ┌───────┴───────┐
                                          │ 素材 & 发布    │
                                          │ 素材文件夹管理  │
                                          │ 手动剪辑发布    │
                                          │ 更新状态标记   │
                                          └───────────────┘
```

**模块间通信：** 数据库字段状态驱动。单条新闻状态流转：`raw` → `translated` → `scored` → `selected` → `drafted` → `published`

**执行方式：** 爬虫和 AI 处理通过 CLI 脚本运行（每天一次），人工审核通过翻文件方式。

---

## 三、目录结构

```
news/
├── data/
│   ├── raw/              ← 爬虫原始数据（JSON）
│   ├── candidates/       ← AI 筛选标注后的候选选题（Markdown）
│   ├── scripts/          ← 用户确认后的视频脚本（Markdown）
│   └── published/        ← 已发布归档
├── assets/               ← 素材库
│   ├── screenshots/      ← 网页截图
│   ├── generated/        ← AI 生成配图/信息图
│   ├── memes/            ← 表情包/网络素材
│   ├── templates/        ← 信息图模板
│   └── index.json        ← 素材索引
├── config/
│   ├── sources.yaml      ← RSS 源配置
│   └── prompts.yaml      ← AI prompt 模板
├── crawlers/             ← 爬虫模块
├── processor/            ← 数据处理模块
├── ai_engine/            ← AI 处理模块
└── cli.py                ← 命令行入口
```

---

## 四、各层详细设计

### 4.1 爬虫层

- **技术：** `feedparser` 解析 RSS/Atom，`httpx` 异步请求抓原文
- **正文提取：** `trafilatura` 从 HTML 提取干净正文
- **频率：** 每天执行一次
- **源分级：** tier1（精选源）, tier2（RSSHub 聚合）, tier3（低频备份）
- **初始源（8-12个）：** Hacker News、TechCrunch、The Verge、Ars Technica、Reddit r/nottheonion、Reddit r/offbeat、Reuters Oddly Enough 等

输出 → `data/raw/YYYY-MM-DD.json`

### 4.2 处理层

- **去重：** 标题相似度 > 85%（`difflib`）判定为重复
- **分类：** AI 批量打标签（科技/AI/互联网/奇闻/其它）
- **翻译：** 英文→中文，技术术语原样+括号注中文，人名公司名保留原文
- **清洗：** 正则 + `trafilatura` 去广告和格式混乱
- **翻译策略：** 长文摘要翻译（≤300字），原文链接保留，方便查证

输出 → `data/raw/YYYY-MM-DD.json`（更新状态）+ `data/candidates/`

### 4.3 AI 层（核心）

**模型：** DeepSeek API（兼容 OpenAI SDK）

#### 4.3.1 选题筛选器
每天几十条 → 初筛 → 5-10 条候选，以 Markdown 文件呈现，包含：
- AI 打分：有趣指数 ⭐、槽点指数 ⭐
- 为什么值得做（冲突/反差/可挖掘性/时效性）
- 建议切入角度
- 原文链接

**筛选维度（AI Prompt）：** 冲突反差感、话题性、可挖掘性、时效性

#### 4.3.2 文案撰写器
用户勾选的选题 → 双版本脚本：

| 版本 | 时长 | 侧重点 | 用途 |
|------|------|--------|------|
| 短视频脚本 | 60-90秒 | 核心槽点、一句话科普、快速吐槽 | 抖音 |
| 长视频脚本 | 5-10分钟 | 背景→逐条分析→资料补全→总结 | B站 |

每个脚本包含：旁白文案 + 画面建议 + 素材清单

#### 4.3.3 素材建议器
自动生成表格：时间点、画面建议、素材来源、优先级

输出 → `data/scripts/[✓] <标题>.md`

### 4.4 素材管理层

```
assets/
├── screenshots/       ← 网页截图（手动或自动）
├── generated/         ← AI 生成的配图/信息图
├── memes/             ← 表情包/网络素材库
├── templates/         ← 信息图模板（可复用）
│   ├── comparison.png
│   ├── timeline.png
│   └── stats.png
└── index.json         ← 素材索引（标签、用途）
```

信息图用 Pillow 生成基础图表（对比表、时间线、数据图）。

### 4.5 人工审核站

第一期无 Web 面板，通过翻 Markdown 文件审阅：
1. 打开 `data/candidates/` 目录
2. 阅读每个候选文件的 AI 标注
3. 想做改文件名为 `[✓]` 前缀标记
4. 运行 `cli.py draft` 生成脚本

---

## 五、CLI 命令

```bash
python cli.py crawl              # 爬取新闻 → data/raw/
python cli.py process            # AI 翻译/分类/筛选 → data/candidates/
python cli.py draft              # 对[✓]选题生成脚本 → data/scripts/
python cli.py run                # 一键执行 crawl → process（推荐日常使用）
```

---

## 六、B站 vs 抖音差异化

| | 抖音 | B站 |
|------|------|------|
| 时长 | 60-90秒 | 5-10分钟 |
| 调性 | 开头3秒抓眼球，快速吐槽 | 深度展开，资料补全 |
| 脚本重点 | 核心槽点+一句总结 | 背景→分析→科普→总结 |
| 画面 | 快节奏切换，文字动画 | 信息图展示，细节讲解 |
| 同一选题 | 做两个版本（快版+深度版） | |

---

## 七、日常工作流

1. 每天：`python cli.py run` → AI 产出候选选题
2. 翻 `data/candidates/` 目录，勾选想做的选题
3. `python cli.py draft` → 生成双版本脚本
4. 在 `data/scripts/` 中修改润色文案
5. 收集素材（截图/AI生成信息图/网络素材）
6. 录音 + 剪辑（手动）
7. 发布到 B站/抖音
8. 归档到 `data/published/`

---

## 八、待定事项

- [ ] 新闻剪辑流程细节（等用户确定剪辑软件和习惯后细化）
- [ ] RSS 源最终清单（第一期跑起来后根据产量调整）
- [ ] DeepSeek API 用量和成本控制策略

---

## 九、复用的现有基础设施

项目将放置在 `E:/Claude code/skill_learn/news/`，可复用现有的：
- `common/` — HTTP 会话管理、请求头、代理、重试、限流
- 现有的爬虫开发经验（bilibili/dangdang 模块）
- `requirements.txt` 可在现有基础上扩展
