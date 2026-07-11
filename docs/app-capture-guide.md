# App 抓包实战指南

使用 mitmproxy 抓取手机 App 的 API 请求，分析接口参数和加密逻辑。

## 一、环境配置

### 1.1 PC 端启动 mitmproxy

```bash
# Web UI 模式（推荐，浏览器查看流量）
mitmweb -s tools/mitm_analyzer.py

# 或命令行模式
mitmdump -s tools/mitm_analyzer.py
```

监听端口: 8080

### 1.2 手机端配置

**iOS:**
1. 设置 → Wi-Fi → 点击当前网络 → 配置代理 → 手动
2. 服务器: PC 的局域网 IP（`ipconfig` 查看）
3. 端口: 8080
4. Safari 打开 `mitm.it` → 下载安装 CA 证书
5. 设置 → 通用 → VPN 与设备管理 → 安装描述文件
6. 设置 → 通用 → 关于本机 → 证书信任设置 → 开启 mitmproxy

**Android:**
1. 设置 → WLAN → 长按当前网络 → 修改网络 → 高级选项
2. 代理: 手动 → 主机名填 PC IP → 端口 8080
3. 浏览器打开 `mitm.it` → 下载安装 CA 证书
4. Android 7+ 需额外步骤: 安装到系统证书区（需 root 或 VirtualXposed）

### 1.3 验证

手机访问任意 HTTPS 网站，mitmweb 界面应出现流量记录。

## 二、实战：抓取 B站 App 投稿接口

### 2.1 操作步骤

1. 启动 mitmweb
2. 手机配置代理 → 安装证书
3. 打开 B站 App → 进入任意 UP 主主页 → 浏览投稿列表
4. mitmweb 中搜索 `/x/space/wbi/arc/search`
5. 查看请求详情: URL、Headers、Query Parameters

### 2.2 典型发现

```
GET /x/space/wbi/arc/search?mid=17076171&ps=20&pn=1&order=pubdate&w_rid=abc123&wts=1234567890
Host: api.bilibili.com
User-Agent: BiliApp/7.0.0 (Android; ...)
Cookie: SESSDATA=...; bili_jct=...
```

对比之前我们用 `requests` 调同一个接口，App 多出了:
- `w_rid`、`wts` — WBI 签名（已实现）
- `BiliApp/7.0.0` UA — 移动端专用
- `Cookie` — 自动登录态

### 2.3 写成 Python

```python
# 完全复制 App 的请求头和参数
headers = {
    "User-Agent": "BiliApp/7.0.0 (Android; ...)",  # 从抓包复制
    "Cookie": "SESSDATA=...; bili_jct=...",         # 从抓包复制
}
resp = requests.get(url, params=signed_params, headers=headers)
```

## 三、常见 App API 特征

| App | 接口特征 | 难点 |
|-----|---------|------|
| B站 | WBI签名 + Cookie | 签名算法已知 |
| 京东 | 自定义加密 body | 需要反编译 App |
| 抖音 | 大量自定义 header + 签名 | 极难 |
| 淘宝 | 复杂鉴权链 | 极难 |
| 小红书 | X-s 签名 | 需要逆向 App |
| 微博 | Cookie + 简单签名 | 简单 |

## 四、工具对比

| | mitmproxy | Charles | Fiddler |
|---|---|---|---|
| 价格 | 免费 | $50 | 免费基础版 |
| 脚本化 | ✅ Python | ❌ | ✅ JScript |
| 平台 | Win/Mac/Linux | Win/Mac | Win |
| HTTPS | ✅ | ✅ | ✅ |
| 推荐度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

## 五、面试话术

"我用 mitmproxy 抓取 App 的 API 请求，分析参数签名逻辑，
然后写 Python 脚本直接调后端接口，跳过了 App 前端的加密层。
比如 B站 UP 主视频接口，我逆向出它 WBI 签名的 img_key/sub_key 混排逻辑，
用 curl_cffi 伪装 TLS 指纹，加 Cookie 登录态绕风控，
实现了无需 App 就能批量获取任意 UP 主全部投稿数据。"
