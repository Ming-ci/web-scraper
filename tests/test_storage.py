"""测试 weather.storage 模块。"""

import csv
from pathlib import Path

from weather.storage import save, CSV_COLUMNS


SAMPLE_DAY = {
    "date": "2026-06-18",
    "city": "北京",
    "city_code": "101010100",
    "weather_desc": "晴",
    "temp_high": 35,
    "temp_low": 22,
    "humidity": "",
    "wind": "北风3级",
}

SAMPLE_DAY_UPDATED = {
    "date": "2026-06-18",
    "city": "北京",
    "city_code": "101010100",
    "weather_desc": "雷阵雨",  # 预报更新了
    "temp_high": 28,
    "temp_low": 18,
    "humidity": "80",
    "wind": "南风4级",
}

SAMPLE_DAY2 = {
    "date": "2026-06-19",
    "city": "北京",
    "city_code": "101010100",
    "weather_desc": "多云",
    "temp_high": 30,
    "temp_low": 20,
    "humidity": 50,
    "wind": "南风2级",
}


class TestSaveFirstWrite:
    """首次写入：创建文件和表头。"""

    def test_creates_file_and_header(self, tmp_path):
        csv_path = tmp_path / "data" / "test.csv"
        save([SAMPLE_DAY], str(csv_path))

        assert csv_path.exists()
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert rows[0] == CSV_COLUMNS
        assert rows[1][0] == "2026-06-18"
        assert rows[1][1] == "北京"

    def test_returns_stats_dict(self, tmp_path):
        """返回统计信息 dict。"""
        csv_path = tmp_path / "test.csv"
        stats = save([SAMPLE_DAY, SAMPLE_DAY2], str(csv_path))
        assert stats["total"] == 2
        assert stats["new"] == 2
        assert stats["updated"] == 0


class TestSaveOverwrite:
    """合并覆盖：同 (date, city) 的新数据覆盖旧数据。"""

    def test_same_date_city_overwrites(self, tmp_path):
        """同日同城再次写入 → 覆盖旧值，不增加行数。"""
        csv_path = tmp_path / "test.csv"

        s1 = save([SAMPLE_DAY], str(csv_path))
        assert s1["new"] == 1
        assert s1["total"] == 1

        # 第二天抓取，同一日期城市，预报更新了
        s2 = save([SAMPLE_DAY_UPDATED], str(csv_path))
        assert s2["new"] == 0
        assert s2["updated"] == 1
        assert s2["total"] == 1  # 行数不变

        # 验证文件内容已更新
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["weather_desc"] == "雷阵雨"
        assert rows[0]["temp_high"] == "28"

    def test_partial_overlap(self, tmp_path):
        """部分重叠：新数据覆盖重叠的，保留不重叠的旧数据。"""
        csv_path = tmp_path / "test.csv"

        # 第一天：6月18日 + 6月19日
        save([SAMPLE_DAY, SAMPLE_DAY2], str(csv_path))

        # 第二天：只更新了 6月18日（预报修正），6月19日没在本次抓取中
        save([SAMPLE_DAY_UPDATED], str(csv_path))

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        # 6月18日被更新，6月19日保留
        assert len(rows) == 2

        row_18 = next(r for r in rows if r["date"] == "2026-06-18")
        row_19 = next(r for r in rows if r["date"] == "2026-06-19")
        assert row_18["weather_desc"] == "雷阵雨"  # 已更新
        assert row_19["weather_desc"] == "多云"     # 未动

    def test_new_date_added(self, tmp_path):
        """新日期在合并时直接追加。"""
        csv_path = tmp_path / "test.csv"

        save([SAMPLE_DAY], str(csv_path))
        stats = save([SAMPLE_DAY2], str(csv_path))

        assert stats["new"] == 1
        assert stats["updated"] == 0
        assert stats["total"] == 2


class TestMultiCity:
    """多城市数据互不影响。"""

    def test_different_city_same_date_independent(self, tmp_path):
        """同日期不同城市独立存储。"""
        csv_path = tmp_path / "test.csv"
        shanghai = dict(SAMPLE_DAY, city="上海", city_code="101020100")

        save([SAMPLE_DAY, shanghai], str(csv_path))

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2

    def test_update_one_city_preserves_other(self, tmp_path):
        """更新北京数据不影响上海数据。"""
        csv_path = tmp_path / "test.csv"
        shanghai = dict(SAMPLE_DAY, city="上海", city_code="101020100")

        save([SAMPLE_DAY, shanghai], str(csv_path))
        save([SAMPLE_DAY_UPDATED], str(csv_path))  # 只更新北京

        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2  # 上海仍存在，北京覆盖了
