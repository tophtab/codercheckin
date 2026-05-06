import pytest

from tests.log_assertions import assert_timestamped_lines
from v2ex import v2ex


def test_get_once_detects_chinese_login_page(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(v2ex, "_fetch_page", lambda url, headers: "需要先登录")

    once, signed, message = v2ex.get_once({}, "V2EX\n")

    assert once is None
    assert signed is False
    assert "unauthenticated or expired" in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert "V2EX daily mission page indicates the cookie is unauthenticated" in output_lines[0]


def test_get_once_detects_english_login_page(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        v2ex,
        "_fetch_page",
        lambda url, headers: "You need to sign in first to view this page",
    )

    once, signed, message = v2ex.get_once({}, "V2EX\n")

    assert once is None
    assert signed is False
    assert "unauthenticated or expired" in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert "V2EX daily mission page indicates the cookie is unauthenticated" in output_lines[0]


def test_get_once_does_not_include_once_token_in_status_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        v2ex,
        "_fetch_page",
        lambda url, headers: "<a href='/mission/daily/redeem?once=secret-once-token'>redeem</a>",
    )

    once, signed, message = v2ex.get_once({}, "V2EX\n")

    assert once == "secret-once-token"
    assert signed is False
    assert "Successfully got once token" in message
    assert "secret-once-token" not in message


def test_check_in_treats_post_redeem_already_claimed_as_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(v2ex, "_fetch_page", lambda url, headers: "每日登录奖励已领取")

    success, message = v2ex.check_in("redacted-once", {}, "V2EX\n")

    assert success is True
    assert "already claimed after redeem request" in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert "V2EX redeem response indicates the daily reward was already claimed" in output_lines[0]
    assert "redacted-once" not in output_lines[0]


def test_check_in_does_not_log_once_token_when_redeem_request_fails(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_fetch_page(url: str, headers: dict[str, str]) -> str:
        raise RuntimeError("network failure including secret-once-token")

    monkeypatch.setattr(v2ex, "_fetch_page", fail_fetch_page)

    success, message = v2ex.check_in("secret-once-token", {}, "V2EX\n")

    assert success is False
    assert "redeem request failed before response classification" in message
    assert "secret-once-token" not in message
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert len(output_lines) == 1
    assert "RuntimeError" in output_lines[0]
    assert "secret-once-token" not in output_lines[0]
