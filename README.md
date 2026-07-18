# Web Scraper — Python 爬虫项目

九个爬虫项目，覆盖 `requests` → `BeautifulSoup` → `Playwright` → `Scrapy` → `AI 流水线` → `API 逆向` 全技术栈。

## 最新成果

- **反爬对抗升级**：TLS 指纹伪装（`curl_cffi`）+ Playwright 无头检测绕过（`stealth.js`），反爬栈增至 7 层
- **B站 UP 主视频爬虫**：WBI 签名 + API 逆向 + Cookie 登录态 + Excel 导出，支持翻页爬取全部投稿
- **AI 新闻流水线**：14 个海外 RSS 源 → DeepSeek 标题翻译 → 人工勾选 → 双版本视频脚本生成

## 项目结构

```
├── common/                    # 反爬 + 工具（8 模块：7层反爬 + captcha验证码 + logger日志）
├── weather/                   # 中国天气网 — requests + BS4（已升级 TLS 伪装）
├── dangdang/                  # 当当商品 — requests + BS4 (GBK)
├── dangdang_scrapy/           # 当当商品 — Scrapy 框架对比版
├── amazon/                    # 亚马逊 — 在线搜索 + 本地双模式（curl_cffi）
├── xiaohongshu/               # 小红书 — 关键词搜索爬虫
├── bilibili/                  # B站 — 排行榜 + 排行榜分区 + UP 主投稿爬虫
│   ├── main.py                #   排行榜 CLI
│   ├── up_videos.py           #   UP 主投稿爬虫（API + Excel）
│   ├── wbi.py                 #   WBI 签名引擎
│   └── auth.py                #   扫码登录 + Cookie 管理
├── news/                      # AI 新闻流水线 — RSS + DeepSeek
│   ├── crawlers/              #   14 源 RSS 采集
│   ├── ai_engine/             #   DeepSeek 翻译/筛选/写稿
│   └── cli.py                 #   CLI 入口
├── dangdang_scrapy_redis/     # 当当商品 — Scrapy-Redis 分布式版
├── playwright_demo/           # Playwright 8 个教学脚本（含 stealth/captcha 对比）
├── tools/                     # 抓包工具（mitmproxy 内联脚本）
├── docs/                      # 6 份技术文档
└── tests/                     # 28 条单元测试
```

## 各项目说明

### bilibili — B站 UP 主投稿爬虫 🆕

通过 B站公开 API（WBI 签名 + TLS 伪装 + Cookie 登录态）爬取任意 UP 主全部投稿，支持 Excel 导出和自动翻页。

```bash
python -m bilibili.auth                                    # 扫码登录（一次性）
python -m bilibili.up_videos --mid 17076171 100 --excel    # 翻页爬取 + 导出 Excel
python -m bilibili.up_videos --file data/xxx.html --excel  # 本地 HTML 导出
```

字段：标题、UP主、MID、BV号、播放量、发布日期。  
技术要点：WBI 签名（img_key/sub_key 混排 + MD5）、`curl_cffi` TLS 指纹伪装、Playwright 扫码登录 + Cookie 持久化、`openpyxl` 格式化输出。

### youtube — YouTube 频道视频 🆕

双引擎设计：yt-dlp（生产级，全字段）/ InnerTube API 逆向（纯 Python，零依赖）。

```bash
python -m youtube.main search gimai_seikatsu --count 50 --excel
python -m youtube.main search gimai_seikatsu --engine innertube --count 50
python -m youtube.main file "data/泛式FunShiki - YouTube.html" --excel
```

逆向要点：首页 `ytcfg.INNERTUBE_API_KEY` → SAPISID Cookie → SHA1 鉴权头 → `youtubei/v1/browse` → `lockupViewModel` 解析。

### amazon — 亚马逊商品搜索 🆕

`curl_cffi` TLS 伪装在线搜索 + 本地 HTML 双模式，提取 ASIN/标题/价格/评分/月销量/链接。

```bash
python -m amazon.main search --keyword Adidas --excel
python -m amazon.main file "data/Amazon.com _ nike.html" --excel
```

### xiaohongshu — 小红书搜索 🆕

从本地 HTML 文件或 Playwright 在线搜索小红书关键词，提取笔记数据。

```bash
python -m xiaohongshu.main file "data/旅游 - 小红书搜索.html" --excel
python -m xiaohongshu.main search --keyword 旅游 --scroll 5 --excel
```

字段：标题、博主昵称、发布时间、点赞数、链接（含 xsec_token）、封面图、抓取时间。

### bilibili — B站排行榜

Playwright 浏览器自动化，点击分区标签抓取排行榜前 100 名。

```bash
python -m bilibili.main --category tech        # 科技分区
python -m bilibili.main --category digital     # 数码分区
```

字段：标题、UP 主、播放量、点赞数、排名、分区、视频链接、封面图、抓取时间。

### news — AI 新闻流水线 🆕

14 个海外 RSS 源 → AI 标题翻译 → 人工勾选 → AI 写双版本脚本（B站长视频 + 抖音短视频）。

```bash
python -m news.cli run --limit 50    # crawl + translate 一键
python -m news.cli translate         # 仅翻译标题
python -m news.cli draft             # 为勾选选题生成脚本
```

RSS 源包括：Hacker News、TechCrunch、The Verge、Ars Technica、Wired、The Register、Engadget、9to5Mac、Boing Boing、Slashdot、Product Hunt、Hackaday、Lobsters、404 Media。  
配置：`news/config/sources.yaml` + `news/config/prompts.yaml`。  
API Key：写入 `news/config/api_key.txt` 或环境变量 `DEEPSEEK_API_KEY`。

### weather — 中国天气网

5 城 7 天预报批量抓取，CSV 合并覆盖，matplotlib 趋势图。**已升级为 TLS 指纹伪装**（`curl_cffi` 替代 `requests`）。

```bash
python -m weather.main collect    # 抓取 → data/weather.csv
python -m weather.main chart      # CSV → data/trend.png
```

### dangdang / dangdang_scrapy — 当当商品搜索

两个版本对比学习：手写 `requests + BS4` vs `Scrapy` 框架（Spider + Pipeline + Feed）。

```bash
python -m dangdang.main --keyword Python --pages 3
cd dangdang_scrapy && scrapy crawl dangdang
```

## 反爬基础设施

`common/` 对所有 HTTP 爬虫通用，已升级至 7 层：

| 层 | 模块 | 技术 | 对抗目标 |
|---|------|------|---------|
| 1 | `headers` | 浏览器头伪装 | 基础 UA 检测 |
| 2 | `throttle` | 请求间隔随机延迟 | 频率检测 |
| 3 | `retry` | 指数退避 + 抖动 | 网络抖动 |
| 4 | `proxy` | IP 代理池轮换 | IP 封禁 |
| 5 | `session` | Cookie 会话管理 | 会话追踪 |
| 6 | `tls` 🆕 | TLS 指纹伪装 (`curl_cffi`) | JA3/JA4 指纹检测 |
| 7 | `stealth` 🆕 | 无头浏览器反检测 | `navigator.webdriver` 检测 |

## 验证码处理

`common/captcha.py` — 统一接口 `solve(source, strategy)`，三策略可选：

| 策略 | 技术 | 适用 |
|------|------|------|
| OCR | Tesseract + Pillow 预处理 | 简单数字/文字验证码 |
| Playwright | 缓动曲线拖拽 + y轴抖动 | 滑块验证码 |
| API | 2captcha 付费平台（~$0.01/次） | 生产环境 |

## 结构化日志

`common/logger.py` — `RotatingFileHandler`（10MB × 3 备份），替代 `print()`：

```
2026-07-11 13:54:59 | INFO    | news.crawlers.rss_fetcher | Hacker News (tech): 20 条
2026-07-11 13:55:01 | WARNING | news.crawlers.rss_fetcher | Reddit (offbeat): 失败 - timeout
```

## Scrapy-Redis 分布式

将单机 Scrapy 改造为多机分布式只需改 3 处：继承 `RedisSpider`、设置 `redis_key`、Redis 调度器+去重。`docker-compose` 设 `replicas: 3` 即启动 3 个并行 Worker。

```bash
cd dangdang_scrapy_redis && scrapy crawl dangdang_redis
docker-compose up --scale worker=3
```

## Docker 部署

多阶段构建：builder 装 pip 包 → runtime 仅保留运行库 + Playwright Chromium。非 root 用户运行。

```bash
docker-compose up -d redis          # Redis 队列
docker-compose run weather          # 天气爬虫
docker-compose run news             # AI 新闻流水线
docker-compose up --scale worker=3  # 分布式 Worker
```

## B站 API 逆向要点

| 技术 | 模块 | 说明 |
|------|------|------|
| WBI 签名 | `bilibili/wbi.py` | img_key + sub_key → 混排 → MD5 签名 |
| TLS 伪装 | `common/tls.py` | `curl_cffi` 模拟 Chrome 124 TLS 指纹 |
| 登录态 | `bilibili/auth.py` | Playwright 扫码 → Cookie 持久化 → 注入 API |

## 测试

```bash
python -m pytest tests/ -v
```

## 技术栈对照

| 引擎 | 适用场景 | 本项目案例 |
|------|---------|----------|
| `requests` + `BS4` | 静态 HTML | weather, dangdang |
| `curl_cffi` | TLS 指纹强检测站 | weather, bilibili API, amazon |
| `Scrapy` | 大规模框架化 | dangdang_scrapy |
| `Playwright` + Cookie | JS 动态渲染 + 登录态 | bilibili, xiaohongshu |
| `Scrapy-Redis` | 分布式爬取 | dangdang_scrapy_redis |
| `feedparser` + AI | RSS 聚合 + 内容生成 | news |
| B站/小红书 API | 公开接口逆向 | bilibili UP 主, xiaohongshu 搜索 |
