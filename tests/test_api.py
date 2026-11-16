"""api 的测试：字段清洗 + 分页逻辑（用 monkeypatch 模拟网络）。"""

from gh_stars.api import fetch_repos, parse_repos


def test_keeps_only_four_fields():
    raw = [
        {
            "name": "linux",
            "stargazers_count": 255610,
            "language": "C",
            "updated_at": "2026-11-14T09:12:33Z",
            "forks": 99999,
            "description": "Linux kernel",
        }
    ]

    result = parse_repos(raw)

    assert result == [
        {
            "name": "linux",
            "stars": 255610,
            "language": "C",
            "updated": "2026-11-14",
        }
    ]
    assert set(result[0]) == {"name", "stars", "language", "updated"}


def test_handles_missing_and_null_fields():
    raw = [
        {"name": "no-lang", "stargazers_count": 3, "language": None,
         "updated_at": "2026-01-02T00:00:00Z"},
        {"name": "no-date", "stargazers_count": 0},
        {},
    ]

    result = parse_repos(raw)

    assert result[0]["language"] == "-"
    assert result[1]["updated"] == ""
    assert result[2] == {"name": "", "stars": 0, "language": "-", "updated": ""}


def test_empty_input_returns_empty_list():
    assert parse_repos([]) == []
class FakeResponse:
    headers = {}

    def __init__(self, data):
        self.status_code = 200
        self._data = data

    def json(self):
        return self._data


def test_fetch_repos_handles_pagination(monkeypatch):
    pages = [
        [{"name": f"r{i}"} for i in range(100)],
        [{"name": "last-1"}, {"name": "last-2"}],
    ]
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(params)
        return FakeResponse(pages[len(calls) - 1])

    monkeypatch.setattr("gh_stars.api.requests.get", fake_get)

    result = fetch_repos("someone")

    assert len(calls) == 2
    assert [c["page"] for c in calls] == [1, 2]
    assert len(result) == 102


def test_fetch_repos_stops_after_short_page(monkeypatch):
    calls = []

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append(params)
        return FakeResponse([{"name": "a"}, {"name": "b"}, {"name": "c"}])

    monkeypatch.setattr("gh_stars.api.requests.get", fake_get)

    result = fetch_repos("tiny")

    assert len(calls) == 1
    assert len(result) == 3