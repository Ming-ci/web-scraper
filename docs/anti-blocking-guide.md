# 爬虫反爬对抗经验总结

基于本项目七个爬虫的实战经验，从零到绕过 B站风控系统的完整技术栈。

## 一、反爬七层模型

从下到上，每层对抗一种检测手段：

```
应用层 (JS)    7. stealth — 隐藏 navigator.webdriver
传输层 (TLS)   6. tls — 伪装浏览器 TLS 指纹
会话层         5. session — Cookie 管理
网络层         4. proxy — IP 代理池轮换
容错层         3. retry — 指数退避 + 抖动
节奏层         2. throttle — 请求间隔随机延迟
表示层 (HTTP)  1. headers — 浏览器头伪装
```

**关键认知**：大多数教程只讲第 1-2 层。真正难啃的站（B站/京东）需要第 6-7 层。

## 二、各层实战要点

### L1-L2: Headers + 节奏

- UA 池至少 5 个真实浏览器指纹，每次随机
- 延迟必须用 `random.uniform()` 而非固定秒数
- 反例：`time.sleep(2)` — 服务器日志里是一条完美规律线
- 正例：`random.uniform(1.0, 3.0)` — 每次间隔不同

### L3: 重试

- 指数退避公式：`delay = base * 2^attempt * random(0.8, 1.2)`
- **必须区分 4xx 和 5xx**：404/403 重试无意义，500/502 重试有效
- 最大重试 3 次，总等待不超过 15 秒

### L4: 代理

- 设计为可选层：无代理时直连，有代理时随机轮换
- 配置文件 + 环境变量双重加载
- 免费代理几乎不可用，生产环境建议付费代理服务

### L5: Session

- `requests.Session()` 自动管理 Cookie，避免每次请求重新握手
- 配合 `pickle` 持久化，脚本重启后保持登录态

### L6: TLS 指纹 ⭐ 关键突破

**问题发现**：同一 URL，`requests` 返回 32KB 内容，`curl_cffi` 返回 170KB。服务器没有返回 403，而是**静默喂了简化版页面**——这种"无声拦截"最难排查。

**根因**：TLS 握手阶段的 JA3 指纹暴露了 `python-urllib3` 身份。

**解决方案**：`curl_cffi` 编译了和 Chrome 一致的 TLS 库，握手特征与真实浏览器无法区分。

```python
# 错误 — JA3 指纹暴露
resp = requests.get(url)

# 正确 — 伪装 Chrome 124
from curl_cffi import requests as cr
resp = cr.get(url, impersonate="chrome124")
```

**验证方法**：`https://tls.browserleaks.com/json` — 查看返回的 `ja3_text` 字段。

### L7: 无头浏览器检测 ⭐

**问题**：Playwright headless 模式下 `navigator.webdriver = true`。

**解决方案**：`page.add_init_script()` 在页面任何脚本执行前注入 JS，覆盖 4 个检测属性：

| 属性 | 无头值 | 正常值 |
|------|--------|--------|
| `navigator.webdriver` | `true` | `false` |
| `window.chrome` | `undefined` | `{runtime:{}, ...}` |
| `navigator.plugins` | `[]` | 3 个内置插件 |
| `navigator.languages` | `['zh-CN']` | `['zh-CN','zh','en']` |

## 三、B站 API 逆向实战 ⭐

### 3.1 WBI 签名

B站公开 API (`/x/space/wbi/arc/search`) 需要签名参数 `w_rid` + `wts`。

**签名流程**：
1. 请求 `/x/web-interface/nav` 获取 `img_url` 和 `sub_url`
2. 从 URL 文件名提取 key（如 `/wbi/7cd084941338...png` → `7cd084941338...`）
3. 拼接两个 key → 按固定映射表 MIXIN_TABLE 重排 → 取前 32 字符
4. 请求参数按 key 排序 → 拼接 URL 查询字符串 → 附加 `wts`(时间戳)
5. `MD5(query_string + signing_key)` → `w_rid`

**坑**：B站曾将字段名从 `img_key`/`sub_key` 改为 `img_url`/`sub_url`，key 嵌入在 URL 路径中。API 字段名可能随时变化，需要关注 B站 API 文档更新。

### 3.2 风控系统绕过

- TLS 指纹伪装过了 API 网关，WBI 签名过了参数校验，但**风控系统**是第三道防线
- 连续多次 API 请求后触发"风控校验失败"（code: -352）
- 解决：注入已登录的 B站 Cookie（`SESSDATA`、`bili_jct`）
- 登录态获取：Playwright 非 headless 模式 → 用户扫码 → 保存 Cookie 到本地 JSON

### 3.3 UP 主投稿接口

```
端点: /x/space/wbi/arc/search
参数: mid=UP主ID, ps=50(每页), pn=页码, order=pubdate
返回: data.list.vlist[] — 含 title, author, bvid, play, created 等
翻页: 当 len(vlist) < ps 时停止
上限: 约 100 条（API 限制，非爬虫限制）
```

### 3.4 编码陷阱汇总

| 站点 | 编码 | 坑 |
|------|------|-----|
| 中国天气网 | UTF-8 | 无 |
| 当当 | **GBK** | 需显式 `resp.encoding='gbk'`，否则中文乱码 |
| B站 | UTF-8 | API 返回正常，CSV 需 `utf-8-sig` (BOM) 兼容 Excel |
| B站 HTML | UTF-8 | Playwright 拿到的已正确解码 |

## 四、CSV/Excel 编码最佳实践

- **CSV**：写入用 `utf-8-sig`（带 BOM），Windows Excel 双击打开不乱码
- **Excel**：`openpyxl` 原生支持 Unicode，无需考虑编码
- **追加 vs 覆盖**：天气数据用"按日期合并覆盖"（预报更新），商品数据用"链接去重跳过"（商品不变）

## 五、架构设计原则

1. **模块单一职责**：fetcher/parser/display/storage 各管各的，换数据源只改 fetcher
2. **反爬层薄封装**：每个反爬模块只暴露 1-2 个函数，接口简单到一行调用
3. **异常三层统一**：`ConnectionError`(网络) → `RuntimeError`(HTTP) → `ValueError`(解析)，CLI 统一捕获
4. **幂等设计**：存储层支持重复运行，不产生脏数据
5. **配置与代码分离**：RSS 源、AI Prompt、API Key 全部走配置文件，不硬编码

## 六、工具选择决策树

```
目标站需要 JS 渲染?
  ├── 是 → Playwright (+ stealth 如果需要)
  └── 否 → 目标站有 TLS 指纹检测?
            ├── 是 → curl_cffi
            └── 否 → requests + BS4

需要规模化(万级+) ?
  └── 是 → Scrapy

需要 RSS 聚合 + AI 内容生成 ?
  └── 是 → feedparser + DeepSeek API
```

## 七、已知限制

- B站空间页 HTML 为 JS 动态渲染，无头浏览器**拿到空壳**，必须走 API
- B站 API 风控系统需要登录态 Cookie，无法纯离线使用
- `curl_cffi` 支持的浏览器指纹有限（Chrome/Safari/Edge），Firefox 部分不可用
- 免费代理几乎不可用，IP 代理层目前为预留架构
