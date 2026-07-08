"""从中国天气网 HTML 页面解析 7 天天气预报。

页面结构（div#7d > ul > li）：
    h1       — 日期（如 "18日（今天）"）
    p[0]     — 天气描述（如 "晴转多云"）
    p[1]     — 温度（今天: "21℃"；未来: "28℃/20℃"，内含 span=高温, i=低温）
    p[2]     — 风力（如 "<3级"）

7天预报页不含湿度数据，humidity 设为 None。
"""

import re
from datetime import datetime, timedelta, date

from bs4 import BeautifulSoup

from common.proxy import get_proxies
from common.retry import retry_on_network_error
from common.tls import get as tls_get

# 城市名 → 编码
CITY_CODES = {
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280101",
    "成都": "101270101",
    "深圳": "101280601",
}

BASE_URL = "http://www.weather.com.cn/weather"


def _parse_li(li, city_name: str, city_code: str, base_date: date, day_offset: int) -> dict:
    """解析单个 li 元素，提取一天的天气预报。

    Args:
        li: BeautifulSoup li 元素
        city_name: 城市中文名
        city_code: 城市编码
        base_date: 今天日期
        day_offset: 相对今天的偏移量（0=今天, 1=明天, ...）

    Returns:
        包含 date, city, city_code, weather_desc, temp_high, temp_low, humidity, wind 的 dict
    """
    # 日期：验证 h1 中的日号与偏移量一致，用于检测页面顺序异常
    h1 = li.find("h1")
    if not h1:
        raise ValueError("日期元素 h1 不存在，页面结构可能已变化。")
    day_str = h1.get_text(strip=True)
    day_match = re.search(r"(\d{1,2})日", day_str)
    if not day_match:
        raise ValueError(f"无法从 '{day_str}' 中提取日期。")

    actual_date = base_date + timedelta(days=day_offset)
    date_str = actual_date.strftime("%Y-%m-%d")

    # p 标签列表
    p_tags = li.find_all("p")
    if len(p_tags) < 3:
        raise ValueError("预报行缺少 p 标签，页面结构可能已变化。")

    # 天气描述：第一个 p
    weather_desc = p_tags[0].get_text(strip=True)
    if not weather_desc:
        weather_desc = "未知"

    # 温度：第二个 p，内容如 "21℃" 或 "28℃/20℃"
    temp_p = p_tags[1]
    temp_span = temp_p.find("span")  # 高温
    temp_i = temp_p.find("i")        # 低温

    if temp_span and temp_i:
        # 未来日：有 span/i 子元素
        temp_high = int(re.sub(r"[^\d-]", "", temp_span.get_text(strip=True)))
        temp_low = int(re.sub(r"[^\d-]", "", temp_i.get_text(strip=True)))
    else:
        # 今天：p 内直接是文本 "21℃"，只有高温，低温统一设 None
        temp_text = temp_p.get_text(strip=True)
        temp_parts = temp_text.split("/")
        if len(temp_parts) == 2:
            temp_high = int(re.sub(r"[^\d-]", "", temp_parts[0]))
            temp_low = int(re.sub(r"[^\d-]", "", temp_parts[1]))
        else:
            temp_high = int(re.sub(r"[^\d-]", "", temp_text))
            temp_low = None  # 今天没有低温预报

    # 风力：第三个 p
    wind = p_tags[2].get_text(strip=True)
    if not wind:
        wind = "未知"

    return {
        "date": date_str,
        "city": city_name,
        "city_code": city_code,
        "weather_desc": weather_desc,
        "temp_high": temp_high,
        "temp_low": temp_low,
        "humidity": None,  # 7天预报页无湿度
        "wind": wind,
    }


@retry_on_network_error(max_retries=3, base_delay=1.0)
def fetch(city_code: str) -> list[dict]:
    """抓取指定城市编码的 7 天天气预报。

    Args:
        city_code: 中国天气网城市编码，如 "101010100"

    Returns:
        list[dict]，每天一条预报，共 7 条

    Raises:
        ConnectionError: 网络不可达
        RuntimeError: HTTP 状态码非 200
        ValueError: HTML 结构与预期不符
    """
    # 反向查找城市名
    city_name = None
    for name, code in CITY_CODES.items():
        if code == city_code:
            city_name = name
            break
    if city_name is None:
        raise ValueError(f"未识别的城市编码：{city_code}")

    url = f"{BASE_URL}/{city_code}.shtml"

    try:
        response = tls_get(
            url, impersonate="chrome124", timeout=10, proxies=get_proxies()
        )
    except Exception as e:
        raise ConnectionError(f"网络请求失败：{e}") from None

    if response.status_code != 200:
        raise RuntimeError(f"请求失败，HTTP 状态码：{response.status_code}")

    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "lxml")

    # 定位 7 天预报容器
    div7d = soup.find("div", id="7d")
    if not div7d:
        raise ValueError("页面未找到 7 天预报容器 div#7d，页面结构可能已变化。")

    uls = div7d.find_all("ul")
    if not uls:
        raise ValueError("7 天预报容器内未找到 ul 列表。")

    lis = uls[0].find_all("li")
    if not lis:
        raise ValueError("预报列表为空。")

    # 以今天为基准，按列表位置偏移得到每天的真实日期（自动处理跨月）
    today = datetime.now().date()

    results = []
    for i, li in enumerate(lis):
        try:
            results.append(_parse_li(li, city_name, city_code, today, i))
        except ValueError:
            continue  # 单行解析失败跳过，不影响其他天

    return results


def fetch_all(city_codes: dict = None) -> list[dict]:
    """抓取多个城市的 7 天预报，合并为一个扁平列表。

    Args:
        city_codes: {城市名: 编码} 字典，默认使用内置 CITY_CODES

    Returns:
        list[dict]，所有城市所有天的预报
    """
    if city_codes is None:
        city_codes = CITY_CODES

    all_data = []
    for city_name, code in city_codes.items():
        try:
            data = fetch(code)
            all_data.extend(data)
        except (ConnectionError, RuntimeError, ValueError) as e:
            print(f"  ✗ {city_name} ({code}) 抓取失败：{e}")
            continue

    return all_data
