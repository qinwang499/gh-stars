"""api 的测试：字段清洗、分页、错误分支（用 monkeypatch 模拟网络）。"""

import pytest
import requests

from gh_stars.api import fetch_repos, parse_repos
from gh_stars.errors import GhStarsError, RateLimitError, UserNotFoundError


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


class FakeResponse404(FakeResponse):
    def __init__(self, data=None):
        super().__init__(data or [])
        self.status_code = 404


class FakeResponse403(FakeResponse):
    def __init__(self, retry_after="30"):
        super().__init__([])
        self.status_code = 403
        self.headers = {"Retry-After": retry_after}


def test_fetch_repos_raises_user_not_found(monkeypatch):
    monkeypatch.setattr(
        "gh_stars.api.requests.get",
        lambda *args, **kwargs: FakeResponse404(),
    )

    with pytest.raises(UserNotFoundError):
        fetch_repos("no-such-user")


def test_fetch_repos_raises_rate_limit(monkeypatch):
    monkeypatch.setattr(
        "gh_stars.api.requests.get",
        lambda *args, **kwargs: FakeResponse403("30"),
    )

    with pytest.raises(RateLimitError) as exc:
        fetch_repos("someone")

    assert exc.value.retry_after == 30


def test_fetch_repos_rate_limit_fallback(monkeypatch):
    monkeypatch.setattr(
        "gh_stars.api.requests.get",
        lambda *args, **kwargs: FakeResponse403("abc"),
    )

    with pytest.raises(RateLimitError) as exc:
        fetch_repos("someone")

    assert exc.value.retry_after == 60


def test_fetch_repos_returns_empty_for_empty_user(monkeypatch):
    monkeypatch.setattr(
        "gh_stars.api.requests.get",
        lambda *args, **kwargs: FakeResponse([]),
    )

    assert fetch_repos("empty-user") == []


class FakeResponse401(FakeResponse):
    def __init__(self):
        super().__init__([])
        self.status_code = 401


def test_fetch_repos_raises_token_error_on_401(monkeypatch):
    monkeypatch.setattr(
        "gh_stars.api.requests.get",
        lambda *args, **kwargs: FakeResponse401(),
    )

    with pytest.raises(GhStarsError, match="token 无效"):
        fetch_repos("someone")


def test_fetch_repos_wraps_connection_error(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("Max retries exceeded / NameResolutionError")

    monkeypatch.setattr("gh_stars.api.requests.get", boom)

    with pytest.raises(GhStarsError, match="连不上"):
        fetch_repos("someone")


def test_fetch_repos_wraps_timeout(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.Timeout("timed out")

    monkeypatch.setattr("gh_stars.api.requests.get", boom)

    with pytest.raises(GhStarsError, match="超时"):
        fetch_repos("someone")