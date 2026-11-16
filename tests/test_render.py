"""render 的测试：排序、宽度计算、CSV 落盘。"""

import csv

from gh_stars.render import _pad, _width, save_csv, sort_by_stars


def _make(stars_list):
    return [{"name": f"r{i}", "stars": s, "language": "C", "updated": "2026-11-14"}
            for i, s in enumerate(stars_list)]


def test_sort_by_stars_desc_and_top():
    repos = _make([5, 100, 30, 7, 60])

    result = sort_by_stars(repos, 3)

    assert [r["stars"] for r in result] == [100, 60, 30]


def test_sort_by_stars_top_larger_than_list():
    repos = _make([1, 2])

    assert len(sort_by_stars(repos, 10)) == 2


def test_width_counts_cjk_as_two():
    assert _width("abc") == 3
    assert _width("张三") == 4
    assert _width("张a") == 3


def test_pad_aligns_by_display_width():
    assert _pad("张三", 6) == "张三  "
    assert len(_pad("张三", 6)) == 4


def test_save_csv_roundtrip(tmp_path):
    path = tmp_path / "out.csv"
    repos = _make([10])

    save_csv(repos, str(path))

    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["name"] == "r0"
    assert rows[0]["stars"] == "10"
def test_sort_by_stars_top_zero_returns_empty():
    repos = _make([5, 100, 30])

    assert sort_by_stars(repos, 0) == []


def test_sort_by_stars_top_negative_drops_last():
    repos = _make([5, 100, 30])

    result = sort_by_stars(repos, -1)

    assert [r["stars"] for r in result] == [100, 30]


def test_sort_by_stars_top_equals_length():
    repos = _make([5, 100, 30])

    result = sort_by_stars(repos, 3)

    assert len(result) == 3
    assert [r["stars"] for r in result] == [100, 30, 5]