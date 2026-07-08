"""测试 weather.china_fetcher 模块。"""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests

from weather.china_fetcher import fetch, fetch_all, CITY_CODES

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _read_html(name: str) -> str:
    """读取 HTML fixture 文件。"""
    path = FIXTURE_DIR / name
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestFetchBeijing:
    """使用北京 HTML fixture 测试正常解析。"""

    def test_returns_7_days(self):
        """北京 fixture 应解析出 7 天预报。"""
        html = _read_html("beijing_7d.html")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("weather.china_fetcher.tls_get", return_value=mock_response):
            result = fetch("101010100")

        assert len(result) == 7

    def test_each_day_has_required_fields(self):
        """每条预报都包含所有必需字段。"""
        html = _read_html("beijing_7d.html")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("weather.china_fetcher.tls_get", return_value=mock_response):
            result = fetch("101010100")

        for day in result:
            assert "date" in day
            assert "city" in day
            assert "city_code" in day
            assert "weather_desc" in day
            assert "temp_high" in day
            assert "temp_low" in day
            assert "humidity" in day
            assert "wind" in day

    def test_city_name_is_beijing(self):
        """城市名应为北京。"""
        html = _read_html("beijing_7d.html")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("weather.china_fetcher.tls_get", return_value=mock_response):
            result = fetch("101010100")

        for day in result:
            assert day["city"] == "北京"
            assert day["city_code"] == "101010100"

    def test_temp_high_is_int(self):
        """高温字段应为 int 类型。"""
        html = _read_html("beijing_7d.html")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("weather.china_fetcher.tls_get", return_value=mock_response):
            result = fetch("101010100")

        for day in result:
            assert isinstance(day["temp_high"], int)


class TestFetchShanghai:
    """用上海 fixture 验证多城市解析。"""

    def test_city_name_is_shanghai(self):
        """上海 fixture 解析出的城市名应为上海。"""
        html = _read_html("shanghai_7d.html")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = html

        with patch("weather.china_fetcher.tls_get", return_value=mock_response):
            result = fetch("101020100")

        for day in result:
            assert day["city"] == "上海"


class TestFetchErrors:
    """异常路径。"""

    def test_invalid_city_code(self):
        """未识别的城市编码抛 ValueError。"""
        with pytest.raises(ValueError, match="未识别的城市编码"):
            fetch("999999999")

    def test_http_error(self):
        """HTTP 非 200 抛 RuntimeError。"""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch("weather.china_fetcher.tls_get", return_value=mock_response):
            with pytest.raises(RuntimeError, match="404"):
                fetch("101010100")

    def test_network_error(self):
        """网络不可达抛 ConnectionError。"""
        with patch("weather.china_fetcher.tls_get",
                   side_effect=requests.exceptions.ConnectionError()):
            with pytest.raises(ConnectionError, match="网络"):
                fetch("101010100")


class TestFetchAll:
    """批量抓取。"""

    def test_fetch_all_limited_cities(self):
        """用 mock 测试 fetch_all，验证城市遍历和合并逻辑。"""
        html = _read_html("beijing_7d.html")

        with patch("weather.china_fetcher.fetch", return_value=[
            {"date": "2026-06-18", "city": "测试", "city_code": "X",
             "weather_desc": "晴", "temp_high": 30, "temp_low": 20,
             "humidity": None, "wind": "1级"}
        ]):
            result = fetch_all({"测试": "X"})
            assert len(result) == 1
            assert result[0]["city"] == "测试"


class TestCITYCODES:
    """城市编码映射。"""

    def test_contains_5_cities(self):
        """内置映射包含 5 个主要城市。"""
        assert len(CITY_CODES) == 5
        assert "北京" in CITY_CODES
        assert "上海" in CITY_CODES
        assert "广州" in CITY_CODES
        assert "成都" in CITY_CODES
        assert "深圳" in CITY_CODES
