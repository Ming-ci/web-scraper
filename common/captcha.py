"""验证码处理 — 统一接口，三策略可选。

策略:
    1. OCR — pytesseract 识别简单文字验证码（需安装 Tesseract）
    2. Playwright — 浏览器模拟滑块/点击验证码
    3. API — 付费打码平台（2captcha/capsolver 等）

用法:
    from common.captcha import solve

    # OCR 识别
    text = solve("data/captcha.png", strategy="ocr")

    # Playwright 滑块（传入 page 对象）
    solve(page, strategy="playwright")

    # 付费 API
    solve("data/captcha.png", strategy="api", api_key="xxx")

面试要点:
    "简单验证码用 OCR，滑块类用 Playwright 模拟，
     生产环境接 2captcha 付费 API，集成在 captcha.py 统一接口下。"
"""

import base64
import os
from pathlib import Path


# === 策略 1: OCR 识别 ===
def _solve_ocr(image_path: str) -> str:
    """用 Tesseract OCR 识别简单文字验证码。"""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(image_path)
        # 预处理：灰度 + 二值化（提高识别率）
        img = img.convert("L")
        img = img.point(lambda x: 0 if x < 128 else 255)

        text = pytesseract.image_to_string(
            img, config="--psm 7 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        )
        return text.strip()
    except ImportError:
        return ""
    except Exception as e:
        print(f"OCR 识别失败: {e}")
        return ""


# === 策略 2: Playwright 滑块模拟 ===
def _solve_playwright(page, slider_selector: str = ".slider", track_selector: str = ".track") -> bool:
    """用 Playwright 模拟人类拖拽滑块。

    Args:
        page: Playwright Page 对象
        slider_selector: 滑块按钮 CSS 选择器
        track_selector: 滑轨 CSS 选择器

    Returns:
        True 表示拖拽完成
    """
    try:
        slider = page.locator(slider_selector)
        track = page.locator(track_selector)

        if not slider.count() or not track.count():
            return False

        # 获取滑轨宽度作为拖拽距离基准
        track_box = track.bounding_box()
        slider_box = slider.bounding_box()
        if not track_box or not slider_box:
            return False

        # 模拟人类拖拽：非匀速，中间有停顿
        target_x = track_box["x"] + track_box["width"] * 0.9
        start_x = slider_box["x"]
        start_y = slider_box["y"] + slider_box["height"] / 2

        page.mouse.move(start_x + 10, start_y)
        page.mouse.down()
        # 分多步移动，模拟加速度变化
        steps = 30
        for i in range(steps):
            progress = i / steps
            # 缓动曲线：先快后慢
            x = start_x + (target_x - start_x) * (progress ** 0.7)
            # 轻微 y 轴抖动
            y = start_y + (1 if i % 5 == 0 else 0)
            page.mouse.move(x, y)
            page.wait_for_timeout(5 + i * 2)  # 逐步减速
        page.mouse.up()

        page.wait_for_timeout(1000)
        return True
    except Exception as e:
        print(f"Playwright 滑块失败: {e}")
        return False


# === 策略 3: 付费打码平台（2captcha / capsolver） ===
def _solve_api(image_path: str, api_key: str = None) -> str:
    """调用第三方打码平台 API。

    示例使用 2captcha（https://2captcha.com）:
        1. 注册获取 api_key
        2. 充值（$3 起）
        3. 调用 solve()

    也支持 capsolver、deathbycaptcha 等平台，调整 URL 即可。
    """
    import requests

    api_key = api_key or os.environ.get("CAPTCHA_API_KEY", "")
    if not api_key:
        print("请设置 CAPTCHA_API_KEY 环境变量")
        return ""

    # 读取图片并 base64 编码
    with open(image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()

    # 2captcha API 流程: submit → wait → get result
    # 提交任务
    resp = requests.post(
        "https://api.2captcha.com/createTask",
        json={
            "clientKey": api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": img_base64,
            },
        },
        timeout=30,
    )
    task_id = resp.json().get("taskId")
    if not task_id:
        print(f"提交失败: {resp.json()}")
        return ""

    # 轮询结果（通常 5-15 秒）
    import time
    for _ in range(20):
        time.sleep(2)
        result_resp = requests.post(
            "https://api.2captcha.com/getTaskResult",
            json={"clientKey": api_key, "taskId": task_id},
            timeout=10,
        )
        data = result_resp.json()
        if data.get("status") == "ready":
            return data.get("solution", {}).get("text", "")
        if data.get("errorId") != 0:
            print(f"打码失败: {data}")
            return ""

    print("打码超时（>40秒）")
    return ""


# === 统一入口 ===
def solve(source, strategy: str = "ocr", **kwargs) -> str | bool:
    """统一验证码处理入口。

    Args:
        source: 图片路径（OCR/API）或 Playwright Page 对象（Playwright）
        strategy: "ocr" | "playwright" | "api"
        **kwargs: 策略特定参数（api_key, slider_selector 等）

    Returns:
        OCR/API 返回识别的文字，Playwright 返回 True/False
    """
    if strategy == "ocr":
        return _solve_ocr(source)
    elif strategy == "playwright":
        return _solve_playwright(source, **kwargs)
    elif strategy == "api":
        return _solve_api(source, api_key=kwargs.get("api_key"))
    else:
        raise ValueError(f"未知策略: {strategy}，可选: ocr / playwright / api")
