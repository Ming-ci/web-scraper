# 变更记录

每次重要修改的时间、位置、原因。完整 diff 使用 `git show <commit>`。

## 2026-07-14

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `aed5d6f` | `bilibili/up_videos.py:from_up_id` | 多线程并发翻页 | 18 页串行需 9s，4 线程并发 2.5s，快 3.6 倍 |

## 2026-07-12

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `214bc01` | `README.md` | 新增验证码/日志/分布式/Docker 章节 | README 落后于代码实现 |

## 2026-07-11

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `3805726` | `docs/agent-reference.md` | 新增小红书章节（5 个踩坑） | 积累小红书 DOM/Cookie/链接/登录/加载经验 |
| `df1edd1` | `xiaohongshu/fetcher.py` | `domcontentloaded` 替代 `networkidle` | 小红书后台请求永不停止导致 30s 超时 |
| `4fcc3b2` | `xiaohongshu/fetcher.py` | Cookie 注入加 `domain` + `path` | `url` 字段无效，Cookie 未生效 |
| `3382215` | `xiaohongshu/auth.py` | 轮询式登录检测替代 `wait_for_url` | `wait_for_url` 误匹配当前 URL，拿到匿名 Cookie |
| `f6b5ee1` | `README.md` | 项目数 7→8，加小红书 | 新增小红书项目 |
| `c1f2bd1` | `xiaohongshu/fetcher.py` | xsec_token 拼接完整链接 | `a:not([class])` 只有基础路径，缺少鉴权参数 |
| `eed41fb` | `xiaohongshu/` 新建 | 小红书搜索爬虫 | `section.note-item` 结构解析 |
| `2a7356e` | `common/captcha.py` | 验证码三策略模块 | OCR/Playwright 滑块/2captcha API 统一接口 |
| `85b0411` | `dangdang_scrapy_redis/` 新建 | Scrapy-Redis 分布式改造 | RedisSpider + 共享队列 + 去重集合 |
| `98e235a` | `tools/mitm_analyzer.py` | mitmproxy 抓包脚本 | 自动记录 API 请求到 JSON |
| `b37a863` | `common/logger.py` | 结构化日志系统 | RotatingFileHandler 替代 print() |
| `b2e0b3e` | `Dockerfile`, `docker-compose.yml` | 容器化部署 | 多阶段构建 + 多服务编排 |
| `2506b62` | `docs/agent-reference.md` | Agent 决策参考手册 | 快速技术选型 + 模板复用 |
| `983b634` | `docs/anti-blocking-guide.md` | 反爬七层经验总结 | B站 API 逆向 + 编码/架构实战 |

## 2026-07-08

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `4631891` | `common/tls.py`, `common/stealth.py`, `bilibili/wbi.py` 等 | 反爬升级至 7 层 + B站 WBI 签名 + UP 主投稿爬虫 | TLS 指纹 + 无头检测 + API 逆向 |

## 2026-07-07

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `33d2c7f` | `news/` 新建 | AI 新闻流水线 | RSS→DeepSeek 翻译→脚本生成 |
| `ba83da9` | `README.md` | 项目结构更新 | 新增 news/Scrapy 项目 |

## 2026-06-27

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `92c24c1` | `bilibili/` | 补全 8 个 CSV 字段 | 缺视频链接和封面图 |
| `bc0c34c` | `bilibili/fetcher.py` 重写 | 排行榜页面结构修正 | `rank` 页面 + 点击分区标签交互 |

## 2026-06-24

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `3dc051f` | `bilibili/` 新建 | B站热门视频爬虫 | Playwright 动态渲染学习 |

## 2026-06-23

| commit | 位置 | 变更 | 原因 |
|--------|------|------|------|
| `9d39f2e` | 项目初始化 | weather + dangdang 爬虫 | 静态 HTML + GBK 编码 |

---

## 回退操作

```bash
git log --oneline                              # 查看所有提交
git show aed5d6f                               # 查看某次修改详情
git diff aed5d6f..c1f2bd1 -- bilibili/         # 对比两次提交中 bilibili/ 的变化
git revert aed5d6f                             # 撤销某次修改（保留历史）
git reset --hard aed5d6f                       # 硬回退到该提交（丢弃后续修改）
```
