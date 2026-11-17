"""cli 与 core 的测试：参数解析、用户名校验。"""

import pytest

from gh_stars.cli import parse_args
from gh_stars.core import validate_username
from gh_stars.errors import UserNotFoundError


def test_parse_args_defaults():
    args = parse_args(["--user", "octocat"])

    assert args.user == "octocat"
    assert args.top == 10
    assert args.output == "stars.csv"
    assert args.verbose is False


def test_parse_args_short_flags_and_verbose():
    args = parse_args(["-u", "torvalds", "-t", "5", "-o", "my.csv", "-v"])

    assert args.user == "torvalds"
    assert args.top == 5
    assert args.output == "my.csv"
    assert args.verbose is True


def test_parse_args_user_is_required():
    with pytest.raises(SystemExit) as exc:
        parse_args([])

    assert exc.value.code == 2


def test_validate_username_strips_spaces():
    assert validate_username("  octocat  ") == "octocat"


def test_validate_username_accepts_dash_and_digits():
    assert validate_username("my-user-2026") == "my-user-2026"


@pytest.mark.parametrize("bad", ["", "   ", "a" * 40, "has space", "bad!"])
def test_validate_username_rejects_bad_input(bad):
    with pytest.raises(UserNotFoundError):
        validate_username(bad)


def test_validate_username_accepts_39_chars():
    name = "a" * 39
    assert validate_username(name) == name
