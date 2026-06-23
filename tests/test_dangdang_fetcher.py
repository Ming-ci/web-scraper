"""测试 dangdang.fetcher 模块。"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dangdang.fetcher import fetch_page, fetch_all

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _read_html(name: str) -> str:
    path = FIXTURE_DIR / name
    with open(path, encoding="utf-8") as f:
        return f.read()


def _mock_session(html: str, status_code: int = 200):
    """创建一个 mock session，其 get() 返回指定 HTML 和状态码。"""
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.text = html
    mock_session = Mock()
    mock_session.get.return_value = mock_resp
    return mock_session


class TestFetchPage:
    """使用 HTML fixture 测试正常解析。"""

    def test_returns_60_items(self):
        html = _read_html("dangdang_python.html")
        mock_session = _mock_session(html)

        with patch("dangdang.fetcher.create_session", return_value=mock_session):
            result = fetch_page("Python")

        assert len(result) == 60

    def test_each_item_has_required_fields(self):
        html = _read_html("dangdang_python.html")
        mock_session = _mock_session(html)

        with patch("dangdang.fetcher.create_session", return_value=mock_session):
            result = fetch_page("Python")

        for item in result:
            assert "title" in item
            assert "price" in item
            assert "comments" in item
            assert "link" in item

    def test_first_item_has_price_yuan(self):
        html = _read_html("dangdang_python.html")
        mock_session = _mock_session(html)

        with patch("dangdang.fetcher.create_session", return_value=mock_session):
            result = fetch_page("Python")

        assert result[0]["price"].startswith("¥")

    def test_first_item_link_is_full_url(self):
        html = _read_html("dangdang_python.html")
        mock_session = _mock_session(html)

        with patch("dangdang.fetcher.create_session", return_value=mock_session):
            result = fetch_page("Python")

        assert result[0]["link"].startswith("http://")


class TestPage2:
    """验证第二页也能正常解析。"""

    def test_page2_returns_60_items(self):
        html = _read_html("dangdang_p2.html")
        mock_session = _mock_session(html)

        with patch("dangdang.fetcher.create_session", return_value=mock_session):
            result = fetch_page("Python", page=2)

        assert len(result) == 60


class TestFetchErrors:
    """异常路径。"""

    def test_http_error(self):
        mock_session = _mock_session("", status_code=404)

        with patch("dangdang.fetcher.create_session", return_value=mock_session):
            with pytest.raises(RuntimeError, match="404"):
                fetch_page("Python")
