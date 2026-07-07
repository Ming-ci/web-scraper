# Web Scraper — Python 爬虫项目

六个爬虫项目，覆盖 `requests` → `BeautifulSoup` → `Playwright` → `Scrapy` → `AI 流水线` 全技术栈，共享反爬基础设施。

## 项目结构

```
├── common/                    # 反爬基础设施（共用 5 模块）
├── weather/                   # 中国天气网 — requests + BS4
├── dangdang/                  # 当当商品 — requests + BS4 (GBK)
├── dangdang_scrapy/           # 当当商品 — Scrapy 改写版
├── bilibili/                  # B站排行榜 — Playwright 动态渲染
├── news/                      # AI 新闻流水线 — RSS + DeepSeek
├── playwright_demo/           # Playwright 7 个教学脚本
└── tests/                     # 23 条单元测试
```

## 各项目说明

### weather — 中国天气网

批量抓取 5 个城市的 7 天天气预报，CSV 合并覆盖，matplotlib 趋势图。

```bash
pip install -r requirements.txt
python -m weather.main collect    # 抓取 → data/weather.csv
python -m weather.main chart      # CSV → data/trend.png
```

### dangdang — 当当商品搜索

搜索当当网商品，多页翻页，GBK 编码处理。

```bash
python -m dangdang.main --keyword Python --pages 3
```

### dangdang_scrapy — 当当 Scrapy 改写版

同一当当爬虫，用 Scrapy 框架重写。对比学习手写 vs 框架差异。

```bash
cd dangdang_scrapy
scrapy crawl dangdang            # 自动输出 CSV，Pipeline 去重
```

### bilibili — B站排行榜

Playwright 浏览器自动化，点击分区标签，抓取排行榜前 100 名。

```bash
python -m bilibili.main --category tech        # 科技分区
python -m bilibili.main --category digital     # 数码分区
python -m bilibili.main --category music       # 音乐分区
```

字段：标题、UP 主、播放量、点赞数、排名、分区、视频链接、封面图、抓取时间。

### news — AI 新闻流水线

14 个海外 RSS 源 → AI 标题翻译 → 人工勾选 → AI 写双版本脚本（B站长视频 + 抖音短视频）。

```bash
python -m news.cli run --limit 50    # crawl + translate 一键
python -m news.cli translate         # 仅翻译标题
python -m news.cli draft             # 为勾选选题生成脚本
```

配置：`news/config/sources.yaml` (RSS源) + `news/config/prompts.yaml` (AI Prompt)。  
API Key：写入 `news/config/api_key.txt` 或设环境变量 `DEEPSEEK_API_KEY`。

### playwright_demo — Playwright 教学脚本

| 脚本 | 概念 |
|------|------|
| `01_launch.py` | 启动浏览器、导航 |
| `02_selectors.py` | CSS 选择器提取 |
| `03_waiting.py` | 等待策略 |
| `04_screenshot.py` | 截图调试 |
| `05_vs_requests.py` | requests vs Playwright 对比 |
| `06_click_type.py` | 输入+点击交互 |
| `07_scroll.py` | 滚动加载 |

```bash
python playwright_demo/01_launch.py
```

## 反爬基础设施

`common/` 对所有 HTTP 爬虫通用：

| 层 | 模块 | 技术 |
|---|------|------|
| 1 | `headers` | 真实浏览器 User-Agent 随机轮换 |
| 2 | `throttle` | 请求间隔随机延迟 |
| 3 | `retry` | 指数退避 + 抖动重试 |
| 4 | `proxy` | IP 代理池轮换 |
| 5 | `session` | `requests.Session` Cookie 管理 |

## 测试

```bash
python -m pytest tests/ -v
```

## 技术栈对照

| 引擎 | 适用场景 | 本项目案例 |
|------|---------|----------|
| `requests` + `BS4` | 静态 HTML | weather, dangdang |
| `Scrapy` | 大规模/框架化 | dangdang_scrapy |
| `Playwright` | JS 动态渲染 | bilibili |
| `feedparser` + AI | RSS 聚合 + 内容生成 | news |
