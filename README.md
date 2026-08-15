# Python Web Scraper �?全栈爬虫工程实践

> **求职意向：爬虫工程师 / 数据采集工程�?*
>
> 独立开发，10 个子项目，覆�?6 种技术引擎，7 层反爬对抗体系�?> 从静�?HTML 解析�?API 逆向，从单机脚本到分布式架构�?> 完整展示爬虫工程师所需�?*全链路能�?*�?
---

## 技术能力矩�?
| 能力维度 | 技术栈 | 对应项目 |
|---------|-------|---------|
| 静态页面解�?| `requests` `BeautifulSoup` `lxml` `curl_cffi` | `weather` `dangdang` `amazon` |
| 动态渲染采�?| `Playwright` `Stealth.js` `持久化Profile` | `bilibili` `shufo` `xiaohongshu` `taobao` |
| 爬虫框架工程�?| `Scrapy` `Scrapy-Redis` `Spider/Pipeline/Feed` | `dangdang_scrapy` `dangdang_scrapy_redis` |
| API 逆向与签�?| `WBI签名` `InnerTube API` `SAPISID鉴权` | `bilibili/wbi.py` `youtube/innertube.py` |
| 反爬对抗 | 7层对抗体系（headers→stealth�?| `common/` |
| AI 集成 | `DeepSeek API` `Prompt工程` `RSS聚合` | `news` |
| 容器化部�?| `Docker` `docker-compose` `多阶段构建` | `Dockerfile` |
| 抓包与协议分�?| `mitmproxy` `HTTPS代理` `证书信任链` | `tools/mitm_analyzer.py` |
| 工程素养 | `pytest` `RotatingFileHandler` `openpyxl` `utf-8-sig` | `tests/` `common/logger.py` |

---

## 项目架构

```
├── common/              # 反爬基础设施�? 层，可复用到任何项目�?├── weather/             # 中国天气�?�?requests + BS4
├── dangdang/            # 当当商品 �?requests + BS4 (GBK编码)
├── dangdang_scrapy/     # 同上 �?Scrapy 框架对比�?├── dangdang_scrapy_redis/ # 同上 �?Scrapy-Redis 分布式版
├── bilibili/            # B�?�?排行�?/ UP主投�?/ WBI签名
├── youtube/             # YouTube �?yt-dlp引擎 + InnerTube逆向
├── xiaohongshu/         # 小红�?�?Playwright + Cookie登录�?├── taobao/              # 淘宝 �?CSS Module解析 + 品牌映射(34品牌)
├── amazon/              # 亚马�?�?curl_cffi TLS伪装 + BS4
├── shufo/               # 佛书�?�?Playwright 动态渲�?├── news/                # AI 新闻流水�?�?14源RSS �?DeepSeek �?脚本
├── tools/               # 辅助工具
├── docs/                # 6 份技术文�?└── tests/               # 28 条单元测�?```

---

## 核心亮点

### 1. 7 层反爬对抗体系（自研，可复用�?
�?HTTP 头伪装到 TLS 指纹伪造，每一层对抗一种检测手段：

| �?| 技�?| 对抗目标 |
|---|------|---------|
| 1 | 浏览器头随机轮换 | UA 特征检�?|
| 2 | 随机延迟 (random.uniform) | 频率检�?|
| 3 | 指数退避重�?(4xx/5xx区分) | 网络抖动 |
| 4 | IP 代理池轮�?| IP 封禁 |
| 5 | Session Cookie 管理 | 会话追踪 |
| 6 | **TLS 指纹伪装 (curl_cffi)** | **JA3/JA4 检�?* |
| 7 | **无头浏览器反检�?(stealth.js)** | **navigator.webdriver** |

**�?6 层实战验证：** 同一 URL，`requests` 返回 32KB（简化版），`curl_cffi` 返回 170KB（完整版）。服务器�?403 拦截，静默返回空数据—�?无声拦截"是日常开发中最难排查的反爬手段�?
### 2. API 逆向（纯 Python，零依赖�?
**B�?WBI 签名�?* 逆向 `img_key + sub_key �?MIXIN_TABLE映射 �?MD5签名` 完整链路，配�?TLS 伪装 + Cookie 登录态，绕过三层风控�?
**YouTube InnerTube�?* �?`ytcfg` 提取 API Key �?SAPISID Cookie SHA1 鉴权 �?`youtubei/v1/browse` 调用 �?`lockupViewModel` 递归解析。不依赖 yt-dlp，完整还�?YouTube 前端 API 调用�?
### 3. 生产级架构思维

- **Docker 多阶段构建：** builder �?runtime 分层，非 root 用户运行
- **docker-compose 编排�?* 6 服务（含 Redis）一键启动，`replicas: 3` 横向扩展
- **结构化日志：** RotatingFileHandler�?0MB×3）替�?`print()`
- **Scrapy-Redis 分布式：** �?3 处即可从单机变多机（RedisSpider + Redis Scheduler + Redis Dedup�?- **幂等存储�?* CSV 按日期合并覆盖（天气）或链接去重（商品）

### 4. AI 集成能力

14 个海�?RSS �?�?DeepSeek 翻译 �?三维评估筛选（有趣/大众/吐槽）→ 双版本脚本生成（B�?5-10 分钟长视�?+ 抖音 60-90 秒短视频）。Prompt 模板化，可配置频道风格�?
---

## 项目列表

| 项目 | 引擎 | 难度 | 核心挑战 |
|------|------|------|---------|
| taobao | BS4 | ⭐⭐⭐⭐�?| CSS Module 动态类�?+ 浏览器自动化 |
| youtube | yt-dlp/InnerTube | ⭐⭐⭐⭐ | API 鉴权逆向 + lockupViewModel 解析 |
| xiaohongshu | Playwright | ⭐⭐⭐⭐ | Cookie 注入 + xesc_token 拼接 |
| bilibili | API/Playwright | ⭐⭐�?| WBI 签名 + 风控绕过 + 多线程翻�?|
| amazon | curl_cffi | ⭐⭐�?| TLS 指纹 + GBK 编码 + 跨语言页面 |
| news | feedparser + AI | ⭐⭐�?| 14 源聚�?+ Prompt 工程 |
| weather | requests | ⭐⭐ | 合并覆盖存储 + matplotlib |
| dangdang | requests/Scrapy | ⭐⭐ | GBK 解码 + Scrapy 对比 |
| shufo | Playwright | ⭐⭐ | 动态渲染翻�?|
| dangdang_redis | Scrapy-Redis | ⭐⭐�?| 分布式队列改�?|

---

## 快速开�?
```bash
pip install -r requirements.txt
playwright install chromium

# 在线抓取示例
python -m youtube.main search gimai_seikatsu --count 50 --excel
python -m bilibili.up_videos --mid 946974 100 --excel
python -m news.cli run --limit 30

# 本地 HTML 解析示例
python -m taobao.main "data/taobao/xxx.html" --excel
python -m amazon.main file "data/amazon/xxx.html" --excel

# 测试
python -m pytest tests/ -v
```

---

## 文档

| 文档 | 内容 |
|------|------|
| `docs/agent-reference.md` | Agent 决策参考手册（技术选型 + 踩坑经验�?|
| `docs/anti-blocking-guide.md` | 反爬七层经验总结 + B�?YouTube API 逆向流程 |
| `docs/app-capture-guide.md` | App 抓包实战（mitmproxy + 手机配置�?|
| `docs/CHANGELOG.md` | 每次修改的时�?位置/原因 |
| `docs/xxxx-design.md` | 新闻自动化流水线设计文档 |

---

*项目持续维护中。所有代码在 macOS/Windows/Linux 均可运行�?
