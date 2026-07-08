# Web Scraper — Python 爬虫项目

七个爬虫项目，覆盖 `requests` → `BeautifulSoup` → `Playwright` → `Scrapy` → `AI 流水线` → `API 逆向` 全技术栈。

## 最新成果

- **反爬对抗升级**：TLS 指纹伪装（`curl_cffi`）+ Playwright 无头检测绕过（`stealth.js`），反爬栈增至 7 层
- **B站 UP 主视频爬虫**：WBI 签名 + API 逆向 + Cookie 登录态 + Excel 导出，支持翻页爬取全部投稿
- **AI 新闻流水线**：14 个海外 RSS 源 → DeepSeek 标题翻译 → 人工勾选 → 双版本视频脚本生成

## 项目结构

```
├── common/                    # 反爬基础设施（7 模块：headers/throttle/retry/proxy/session/tls/stealth）
├── weather/                   # 中国天气网 — requests + BS4（已升级 TLS 伪装）
├── dangdang/                  # 当当商品 — requests + BS4 (GBK)
├── dangdang_scrapy/           # 当当商品 — Scrapy 框架对比版
├── bilibili/                  # B站 — 排行榜 + 排行榜分区 + UP 主投稿爬虫
│   ├── main.py                #   排行榜 CLI
│   ├── up_videos.py           #   UP 主投稿爬虫（API + Excel）
│   ├── wbi.py                 #   WBI 签名引擎
│   └── auth.py                #   扫码登录 + Cookie 管理
├── news/                      # AI 新闻流水线 — RSS + DeepSeek
│   ├── crawlers/              #   14 源 RSS 采集
│   ├── ai_engine/             #   DeepSeek 翻译/筛选/写稿
│   └── cli.py                 #   CLI 入口
├── playwright_demo/           # Playwright 8 个教学脚本（含 stealth 对比）
└── tests/                     # 23 条单元测试
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
| `curl_cffi` | TLS 指纹强检测站 | weather (已升级), bilibili API |
| `Scrapy` | 大规模框架化 | dangdang_scrapy |
| `Playwright` | JS 动态渲染 | bilibili 排行榜, auth 登录 |
| `feedparser` + AI | RSS 聚合 + 内容生成 | news |
| B站 WBI API | 公开接口逆向 | bilibili UP 主投稿 |
