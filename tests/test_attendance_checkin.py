from types import SimpleNamespace

import pytest

from attendance_checkin import AttendanceConfig, run_attendance_checkin
from tests.log_assertions import assert_timestamped_lines


CONFIG = AttendanceConfig(
    name="TESTSITE",
    env_name="TEST_COOKIE",
    domains=["example.com"],
    origin="https://example.com",
    referer="https://example.com/board",
    attendance_url="https://example.com/api/attendance?random=true",
)


def test_run_attendance_checkin_posts_each_cookie_with_timeout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = []
    notifications = []

    def post(url, *, headers, impersonate, timeout):
        calls.append(
            {
                "url": url,
                "cookie": headers["Cookie"],
                "impersonate": impersonate,
                "timeout": timeout,
            }
        )
        return SimpleNamespace(status_code=200, text='{"success": true}')

    result = run_attendance_checkin(
        CONFIG,
        get_cookie=lambda env_name, domains: "a=1 & b=2",
        notify=notifications.append,
        sleep=lambda seconds: None,
        randint=lambda start, end: 1,
        post=post,
    )

    assert result == 0
    assert calls == [
        {
            "url": CONFIG.attendance_url,
            "cookie": "a=1",
            "impersonate": "chrome136",
            "timeout": 30,
        },
        {
            "url": CONFIG.attendance_url,
            "cookie": "b=2",
            "impersonate": "chrome136",
            "timeout": 30,
        },
    ]
    assert notifications == [
        "TESTSITE account 1 check-in successful",
        "TESTSITE account 2 check-in successful",
    ]
    output_lines = assert_timestamped_lines(capsys.readouterr().out)
    assert any("Using the 1 account for check-in..." in line for line in output_lines)
    assert any("TESTSITE account 2 check-in successful" in line for line in output_lines)


def test_run_attendance_checkin_returns_failure_on_business_error() -> None:
    notifications = []

    def post(url, *, headers, impersonate, timeout):
        return SimpleNamespace(status_code=200, text='{"success": false, "message": "bad cookie"}')

    result = run_attendance_checkin(
        CONFIG,
        get_cookie=lambda env_name, domains: "a=1",
        notify=notifications.append,
        sleep=lambda seconds: None,
        randint=lambda start, end: 1,
        post=post,
    )

    assert result == 1
    assert notifications == [
        'TESTSITE account 1 check-in failed, response content: {"success": false, "message": "bad cookie"}'
    ]


def test_run_attendance_checkin_rejects_empty_cookie() -> None:
    with pytest.raises(ValueError, match="TEST_COOKIE"):
        run_attendance_checkin(
            CONFIG,
            get_cookie=lambda env_name, domains: "",
            notify=lambda message: True,
        )
