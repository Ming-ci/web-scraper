# Agent Reference: 爬虫技术决策手册

给 Agent 使用的快速参考。收到抓取任务时，按此流程决策。

## 1. 快速分类

收到 URL 后，先判断页面类型：

| 信号 | 判断为 | 用 |
|------|--------|-----|
| 页面含 `<script>window.__INITIAL_STATE__` 或 `__NEXT_DATA__` | SSR/预渲染 | `requests` + BS4（直接解析 JSON） |
| `<div id="app">` 或大量 `<script>` 无内容 | SPA/JS渲染 | Playwright |
| URL 含 `/api/` 或返回 JSON | API | `curl_cffi` + WBI签名(若B站) |
| 页面后缀 `.shtml` / `.html` / `.do` | 传统服务端渲染 | `requests` + BS4 |
| RSS/Atom feed URL | RSS | `feedparser` + `httpx`(带timeout) |
| 批量采集(万级+) | 工程化 | Scrapy |

## 2. 编码检测

| URL 特征 | 编码 | 处理方式 |
|----------|------|----------|
| 中国网站 (`.com.cn`, `dangdang`, `weather.com.cn`) | **GBK** | `resp.encoding = 'gbk'` 再传 BS4 |
| 国际站 / API | UTF-8 | 默认即可 |
| B站 API | UTF-8 | 默认 |
| B站 HTML | UTF-8 | Playwright 自动处理 |

检查方法: 先发请求 → `resp.apparent_encoding` → 如果不是 utf-8 就手动设置。

## 3. 反爬层选择

按目标站反爬强度选层数：

| 强度 | 目标站特征 | 需要的层 |
|------|-----------|---------|
| 低 | 天气网、当当 | L1(headers) + L2(throttle) |
| 中 | RSS 源、社区站 | + L3(retry) + L5(session) |
| 高 | B站 API、京东 | + L6(tls/curl_cffi) |
| 极高 | B站空间页(HTML)、淘宝 | + L7(stealth) 或 Cookie登录态 |

## 4. 项目模板选择

收到抓取任务后，对照已有项目选最接近的作为模板：

| 任务特征 | 参考项目 | 复用文件 |
|---------|---------|---------|
| 静态 HTML 列表型数据 | `weather/china_fetcher.py` | BS4 解析模式 + 分页 |
| API 调用拿列表 | `bilibili/wbi.py` + `up_videos.py` | 签名 + 翻页 + Excel导出 |
| JS 渲染需要交互(点击/输入) | `bilibili/main.py` (排行榜) | Playwright + CSS选择器 |
| RSS 聚合 + AI 处理 | `news/` | feedparser + AI pipeline |
| 需要登录态 + JS渲染搜索 | `xiaohongshu/` | Playwright + Cookie + BS4解析 |
| API 逆向 + bot检测强 | `youtube/` | InnerTube 逆向 或 yt-dlp引擎 |
| 需要登录态 | `bilibili/auth.py` | Playwright 扫码 + Cookie持久化 |
| 需要框架化 | `dangdang_scrapy/` | Scrapy Spider + Pipeline |

## 5. 标准模块接口

所有新建爬虫项目遵循以下接口约定：

### fetcher 模块
```python
# 输入参数 → 返回 list[dict]，异常统一抛 ConnectionError/RuntimeError/ValueError
def fetch(some_param) -> list[dict]:
    ...
```

### storage 模块
```python
# 返回新增条数
def save(data: list[dict], filepath: str) -> int:
    ...
```

### CLI 模块
```python
# argparse + 子命令模式
def main():
    parser = argparse.ArgumentParser(...)
    subparsers = parser.add_subparsers(dest="command")
    ...
```

### 测试模式
```
tests/
├── fixtures/xxx.html        # 真实页面快照
├── test_xxx_fetcher.py      # mock 网络请求，fixture 测解析
```

## 6. BS4 选择器速查

| 需求 | 写法 |
|------|------|
| 按 class 找 | `soup.select('.class-name')` |
| 按 tag + class | `soup.select('div.class-name')` |
| 按 id 找(数字id) | `soup.find('div', id='7d')` （不能用 CSS 选择器） |
| 提取属性 | `el.get('href', '')` |
| 提取文本 | `el.get_text(strip=True)` |
| 提取特定子元素文本 | `el.select_one('.sub::text')` 然后 `.get()` |

## 7. Playwright 模式速查

| 场景 | 代码 |
|------|------|
| 启动 | `browser = p.chromium.launch(headless=True)` |
| 导航 | `page.goto(url, wait_until='networkidle')` — 若 timeout 改用 `domcontentloaded` |
| Cookie注入 | `context.add_cookies([{name,value,domain,path}])` **必须带 domain+path** | 
| 等待元素 | `page.wait_for_selector(sel, timeout=10000)` |
| 点击 | `locator.click()` |
| 输入 | `locator.fill('text')` |
| 滚动加载 | `page.evaluate('window.scrollTo(0, document.body.scrollHeight)')` |
| 提取HTML | `page.content()` → 传给 BS4 解析 |
| CSS 选择器 | `page.locator(sel).all()` |
| 反检测 | `apply_stealth(page)` 必须在 `page.goto()` 之前 |

## 8. Excel 导出模式

```python
from openpyxl import Workbook
wb = Workbook()
ws = wb.active
ws.append(["表头1", "表头2", ...])
for item in data:
    ws.append([item["k1"], item["k2"], ...])
ws.column_dimensions["A"].width = 宽
wb.save(path)
```

## 9. 常见翻页模式

| 模式 | 实现 |
|------|------|
| URL 参数 `?page=N` | `for page in range(1, max+1): request(url + f'?page={page}')` |
| URL 路径 `/list/N` | 同上，拼接路径 |
| API 分页 `pn=N, ps=N` | `while len(results) < limit: api(params={'pn': page}); page+=1` |
| 滚动加载 | Playwright `page.evaluate('window.scrollTo(...)')` + 计数器 |
| 点击"加载更多" | Playwright `locator.click()` → `wait_for_selector` 循环 |

## 10. 小红书特定经验

- **搜索 URL**: `https://www.xiaohongshu.com/search_result?keyword={kw}&source=web_search_result_notes`
- **DOM 结构**: `section.note-item` → `.title` / `.name` / `.time` / `.count` / `a.cover img` / `a:not([class])`
- **封面图**: `a.cover img` 的 `src`，线上是真实 URL（`sns-webpic-qc.xhscdn.com`），本地保存是相对路径
- **帖子链接**: `a:not([class])` 获取 `/explore/{id}` 基础链接，再从 `a.cover` 的 href 中提取 `xsec_token`，拼接完整 URL: `/explore/{id}?xsec_token=...&xsec_source=pc_search&source=web_explore_feed`
- **Cookie 注入**: `context.add_cookies()` 必须带 `domain: ".xiaohongshu.com"` 和 `path: "/"`，不能用 `url` 字段
- **登录检测**: 用轮询检测"登录"按钮是否消失，**不要用 `wait_for_url`**（当前 URL 已匹配立即返回，导致误判已登录）
- **页面加载**: 用 `wait_until="domcontentloaded"` 而非 `networkidle`（小红书后台请求永不停止导致 timeout）
- **搜索模式**: Playwright + stealth + Cookie 登录态，本地 HTML 用纯 BS4

## 11. B站特定经验

- **排行榜**: URL `/v/popular/rank`，分区通过**点击标签**切换（非 URL 参数），DOM 是 `li.rank-item`
- **UP主空间页 HTML**: JS 动态渲染 + 登录墙，**不要用 Playwright 直接抓**，走 API
- **API 签名**: `/x/web-interface/nav` → 提取 `img_url/sub_url` 中的 key → MIXIN_TABLE 混排 → MD5
- **风控**: 连续 API 调用触发 code:-352，需要 `bilibili/auth.py` 登录后获取 Cookie
- **UP主 mid**: 从 `space.bilibili.com/{mid}` URL 获取，或从 HTML 的 `<a href="space.bilibili.com/...">` 提取

## 11. YouTube / InnerTube API 逆向

- **首页 ytcfg**: `ytcfg.set({...})` 含 `INNERTUBE_API_KEY`, `INNERTUBE_CONTEXT`, `VISITOR_DATA`
- **鉴权公式**: `SAPISIDHASH = "{timestamp}_{sha1(ts + SAPISID + origin)}"` — SAPISID 从 Cookie 提取
- **API 端点**: `POST youtubei/v1/browse?key={api_key}` → body=`{context, browseId:UCxxx}`
- **数据格式**: YouTube 2026 新版使用 `lockupViewModel`（非旧版 `videoRenderer`）
- **解析 lockupViewModel**: 
  - title → `metadata.lockupMetadataViewModel.title.content`
  - duration → `overlays[].thumbnailBottomOverlayViewModel.badges[].thumbnailBadgeViewModel.text`
  - views/time → `metadata.lockupMetadataViewModel.metadata.content.rows`
  - videoId → 从封面图 URL 正则 `/vi/(\w+)/`
- **双引擎策略**: yt-dlp（生产，全字段）+ InnerTube 逆向（面试展示，零依赖）
- **bot 检测**: YouTube 对 curl_cffi/Playwright 均有强检测，`ytInitialData` 虽在 HTML 中但无 `videoRenderer`，走 InnerTube API 是唯一可靠路径。
- **代理**: 国内需配置代理访问，Playwright `launch` 参数 `proxy={"server": "http://127.0.0.1:7890"}` 或 curl_cffi `proxy=` 参数

## 12. 新任务清单

收到新的抓取 URL 时，按序执行：

```
[ ] 1. 发一个 requests.get → 看 status_code 和 content 长度
[ ] 2. 检查 resp.apparent_encoding，如果非 utf-8 则切换
[ ] 3. 看 HTML 是否有核心数据 → 有则 BS4，没有则 Playwright
[ ] 4. 如果 URL 含 /api/ 或返回 JSON → 走 API 路线，检查是否需要签名
[ ] 5. 有登录墙 → 用 Playwright auth.py 模式
[ ] 6. 对照本文件第 4 节选模板项目复用
[ ] 7. 按第 5 节接口约定写模块
[ ] 8. 保存一份 HTML fixture 到 tests/fixtures/ → 写测试
[ ] 9. CSV 用 'utf-8-sig', Excel 用 openpyxl, GBK站写 resp.encoding='gbk'
```
