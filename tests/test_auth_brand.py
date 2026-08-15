"""测试 auth seam、品牌映射与 youtube 深模块。"""

from common.auth import flatten_jar, has_cookies, jar_to_playwright, load_jar, save_jar
from taobao.brand_map import extract_brand
from youtube.channel import _normalize

JAR = [
    {"name": "SESSDATA", "value": "abc", "domain": ".bilibili.com", "path": "/"},
    {"name": "bili_jct", "value": "xyz", "domain": ".bilibili.com", "path": "/"},
]


class TestAuthJar:
    """common.auth jar 往返与格式转换。"""

    def test_save_load_roundtrip_preserves_domain_path(self, tmp_path):
        p = tmp_path / "cookies.json"
        save_jar(p, JAR)
        jar = load_jar(p)

        assert jar == JAR  # domain/path 不被丢弃

    def test_flatten(self):
        flat = flatten_jar(JAR)
        assert flat == {"SESSDATA": "abc", "bili_jct": "xyz"}

    def test_jar_to_playwright_preserves_existing(self):
        pw = jar_to_playwright(JAR, domain=".fallback.com")
        assert pw[0]["domain"] == ".bilibili.com"  # 原值优先

    def test_jar_to_playwright_fills_missing_domain(self):
        jar = [{"name": "web_session", "value": "v"}]
        pw = jar_to_playwright(jar, domain=".xiaohongshu.com")
        assert pw[0]["domain"] == ".xiaohongshu.com"
        assert pw[0]["path"] == "/"

    def test_missing_file(self, tmp_path):
        assert load_jar(tmp_path / "nope.json") == []
        assert not has_cookies(tmp_path / "nope.json")

    def test_has_cookies(self, tmp_path):
        p = tmp_path / "cookies.json"
        save_jar(p, JAR)
        assert has_cookies(p)

    def test_corrupt_file_returns_empty(self, tmp_path):
        p = tmp_path / "cookies.json"
        p.write_text("{not json", encoding="utf-8")
        assert load_jar(p) == []


class TestBrandMap:
    """taobao 品牌映射独立模块。"""

    def test_chinese_brand(self):
        assert extract_brand("耐克 运动鞋") == "Nike/耐克"

    def test_english_brand(self):
        assert extract_brand("Nike Air Max") == "Nike/耐克"

    def test_alias(self):
        assert extract_brand("三叶草经典款") == "Adidas/阿迪达斯"

    def test_unknown_brand(self):
        assert extract_brand("某不知名品牌") == "其他"


class TestYoutubeNormalize:
    """youtube channel 深模块字段不变式。"""

    def test_fills_missing_fields(self):
        items = [{"title": "t1", "views": "1", "link": "l1"}]
        out = _normalize(items)

        assert out[0]["pub_time"] == ""
        assert out[0]["channel"] == ""
        assert out[0]["scrape_time"] == ""

    def test_keeps_present_fields(self):
        items = [{"title": "t1", "channel": "c1"}]
        out = _normalize(items)
        assert out[0]["channel"] == "c1"

    def test_all_fields_constant_shape(self):
        out = _normalize([{"title": "x"}])
        assert set(out[0].keys()) == {
            "title", "views", "pub_time", "duration", "link", "channel", "scrape_time",
        }
