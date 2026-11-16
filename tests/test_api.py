"""api.parse_repos 的测试：纯函数，不需要联网。"""

from gh_stars.api import parse_repos


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
