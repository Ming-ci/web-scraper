# 多阶段构建 — Python 爬虫项目
# 阶段 1: 构建依赖
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .

# 安装编译依赖（curl_cffi 需要 libcurl-dev）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libcurl4-openssl-dev libssl-dev \
    && pip install --user --no-cache-dir -r requirements.txt \
    && apt-get remove -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# 阶段 2: 运行环境
FROM python:3.11-slim

WORKDIR /app

# 1. curl_cffi 运行库
# 2. 中文字体 (matplotlib)
# 3. Playwright 放到下一层，用官方 install-deps 自动处理系统库
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcurl4 fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 安装 Playwright (仅 Chromium，--with-deps 自动装系统库)
RUN pip install --no-cache-dir playwright && \
    python -m playwright install --with-deps chromium && \
    pip uninstall -y playwright

# 复制 Python 包
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# 复制项目文件
COPY common/ ./common/
COPY weather/ ./weather/
COPY dangdang/ ./dangdang/
COPY bilibili/ ./bilibili/
COPY news/ ./news/
COPY playwright_demo/ ./playwright_demo/
COPY tests/ ./tests/

# 环境变量默认值（运行时覆盖）
ENV PYTHONIOENCODING=utf-8
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

# 非 root 用户（安全最佳实践）
RUN useradd -m -s /bin/bash scraper && chown -R scraper:scraper /app
USER scraper

# 默认：运行天气爬虫
CMD ["python", "-m", "weather.main", "collect"]
