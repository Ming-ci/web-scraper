# Web Scraper — Python 爬虫项目

中国天气网批量抓取 + 当当网商品搜索，共享反爬基础设施，支持 CSV 持久化与 matplotlib 可视化。

## 项目结构

```
├── common/                    # 反爬基础设施（共用）
│   ├── headers.py             # 浏览器头伪装
│   ├── throttle.py            # 请求节奏控制
│   ├── retry.py               # 指数退避重试
│   ├── proxy.py               # IP 代理池轮换
│   └── session.py             # Cookie 持久化
├── weather/                   # 中国天气网爬虫
│   ├── china_fetcher.py       # HTML 解析器（BeautifulSoup + lxml）
│   ├── storage.py             # CSV 合并写入
│   ├── scheduler.py           # 多城市批量编排
│   ├── chart.py               # matplotlib 温度趋势图
│   └── main.py                # CLI 入口
├── bilibili/                  # B站热门视频爬虫（Playwright）
│   ├── fetcher.py             # 浏览器自动化 + BS4 解析
│   ├── storage.py             # CSV 去重写入
│   └── main.py                # CLI 入口
├── dangdang/                  # 当当网商品爬虫
│   ├── fetcher.py             # 搜索页解析器（BeautifulSoup + lxml）
│   ├── storage.py             # CSV 去重写入
│   └── main.py                # CLI 入口
├── tests/                     # 单元测试（pytest）
│   ├── fixtures/              # HTML/JSON 快照
│   ├── test_china_fetcher.py
│   ├── test_storage.py
│   └── test_dangdang_fetcher.py
└── data/                      # 数据输出目录
```

## 环境安装

```bash
pip install -r requirements.txt
```

## 使用方式

### 天气爬虫 —— 中国天气网

批量抓取 5 个城市的 7 天天气预报，写入 CSV，生成温度趋势图。

```bash
python -m weather.main collect              # 抓取 5 城 → data/weather.csv
python -m weather.main chart                # CSV → data/trend.png
```

数据来源：`weather.com.cn`（静态 HTML，BeautifulSoup + lxml 解析）。  
覆盖城市：北京、上海、广州、成都、深圳。  
CSV 策略：按 `(日期, 城市)` 合并覆盖 —— 再次抓取时更新已有预报，保留历史记录，新增最新一天。

### 当当爬虫 —— 商品搜索

搜索当当网商品，支持多页，写入 CSV。

```bash
python -m dangdang.main --keyword Python --pages 3
```

数据来源：`search.dangdang.com`（静态 HTML，GBK 编码）。  
抓取字段：商品名称、价格、评论数、商品链接。

### B站爬虫 —— 热门视频（Playwright）

使用 Playwright 浏览器自动化抓取 B 站热门视频，支持滚动加载更多。

```bash
python -m bilibili.main --scroll 3
```

数据来源：`bilibili.com/v/popular/all`（JavaScript 动态渲染，必须 Playwright）。  
抓取字段：视频标题、UP 主、播放量、点赞数、视频链接、封面图。  
技术特点：真实浏览器渲染、滚动加载、`BeautifulSoup` 二次解析。

### 运行测试

```bash
python -m pytest tests/ -v
```

## 技术要点

### 反爬层

`common/` 提供五层反爬，对任意 HTTP 爬虫通用：

| 层 | 模块 | 技术 |
|---|------|------|
| 1 | `headers` | 真实浏览器 User-Agent 随机轮换 |
| 2 | `throttle` | 请求间隔随机延迟（1–3s） |
| 3 | `retry` | 指数退避 + 随机抖动，最多 3 次重试 |
| 4 | `proxy` | 从文件或环境变量加载 IP 代理池，随机轮换 |
| 5 | `session` | `requests.Session` 管理 Cookie，支持持久化 |

### CSV 编码

输出 CSV 使用 `utf-8-sig` 编码（UTF-8 + BOM），兼容 Windows Excel 直接打开。

### 数据流

```
weather.main collect  →  scheduler.collect()
                              → china_fetcher.fetch(code) × 5 个城市
                              → storage.save(全部数据)
                              → data/weather.csv

weather.main chart    →  chart.draw()
                              → data/trend.png

dangdang.main         →  fetcher.fetch_page(keyword, page) × N 页
                              → storage.save(全部数据)
                              → data/dangdang.csv
```

### 异常约定

所有 fetcher 模块使用三种统一的异常类型：
- `ConnectionError` — 网络故障
- `RuntimeError` — HTTP 非 200 状态码
- `ValueError` — 页面结构异常

CLI 统一捕获并输出友好提示，不暴露异常堆栈。
