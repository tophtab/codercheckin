from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

import scheduler
from checkin_runner import TargetExecutionError


def test_format_timestamp_uses_readable_local_timezone() -> None:
    timestamp = datetime(2026, 4, 29, 3, 30, 0, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert (
        scheduler.format_timestamp(timestamp)
        == "2026-04-29 03:30:00 Asia/Shanghai (UTC+08:00)"
    )


def test_load_schedule_config_uses_default_0330(
    monkeypatch,
) -> None:
    monkeypatch.delenv("CHECKIN_CRON", raising=False)
    monkeypatch.delenv("TZ", raising=False)

    cron_expression, timezone_name, timezone = scheduler.load_schedule_config()

    assert cron_expression == "30 3 * * *"
    assert timezone_name == "Asia/Shanghai"
    assert timezone == ZoneInfo("Asia/Shanghai")


def test_sleep_until_logs_wait_status_periodically(capsys) -> None:
    timezone = ZoneInfo("Asia/Shanghai")
    current_time = datetime(2026, 4, 29, 1, 0, 0, tzinfo=timezone)
    target_time = current_time + timedelta(hours=1, minutes=1)

    def now() -> datetime:
        return current_time

    def sleep(seconds: float) -> None:
        nonlocal current_time
        current_time += timedelta(seconds=seconds)

    scheduler.sleep_until(
        target_time,
        sleep=sleep,
        now=now,
        status_log_interval_seconds=60 * 60,
    )

    output = capsys.readouterr().out
    assert (
        "Waiting for next run at 2026-04-29 02:01:00 Asia/Shanghai (UTC+08:00) "
        "(1h 1m remaining)"
    ) in output
    assert (
        "Waiting for next run at 2026-04-29 02:01:00 Asia/Shanghai (UTC+08:00) "
        "(1m remaining)"
    ) in output


def test_main_propagates_target_failure(monkeypatch, capsys) -> None:
    timezone = ZoneInfo("Asia/Shanghai")
    next_run = datetime(2026, 4, 29, 3, 30, 0, tzinfo=timezone)
    sleep_calls = []

    monkeypatch.setattr(
        scheduler,
        "load_schedule_config",
        lambda: ("30 3 * * *", "Asia/Shanghai", timezone),
    )
    monkeypatch.setattr(scheduler, "parse_targets", lambda: ["v2ex"])
    monkeypatch.setattr(scheduler, "validate_target_cookies", lambda targets: None)
    monkeypatch.setattr(scheduler, "get_next_run", lambda now, cron: next_run)
    monkeypatch.setattr(scheduler, "sleep_until", sleep_calls.append)

    def fail_run_targets(targets: list[str]) -> int:
        raise TargetExecutionError(
            target="v2ex",
            returncode=7,
            recent_output=[("stderr", "actual error string: cookie expired")],
        )

    monkeypatch.setattr(scheduler, "run_targets", fail_run_targets)

    with pytest.raises(TargetExecutionError, match="actual error string: cookie expired"):
        scheduler.main()

    assert sleep_calls == [next_run]

    output = capsys.readouterr().out
    assert "Next run scheduled at 2026-04-29 03:30:00 Asia/Shanghai (UTC+08:00)" in output
    assert "Scheduled check-in failed at " in output


def test_main_validates_target_cookies_before_waiting(monkeypatch) -> None:
    timezone = ZoneInfo("Asia/Shanghai")
    calls = []

    monkeypatch.setattr(
        scheduler,
        "load_schedule_config",
        lambda: ("30 3 * * *", "Asia/Shanghai", timezone),
    )
    monkeypatch.setattr(scheduler, "parse_targets", lambda: ["nodeseek"])

    def fail_validation(targets: list[str]) -> None:
        calls.append(("validate", targets))
        raise ValueError("startup validation failed")

    monkeypatch.setattr(scheduler, "validate_target_cookies", fail_validation)
    monkeypatch.setattr(
        scheduler,
        "sleep_until",
        lambda target_time: calls.append(("sleep", target_time)),
    )

    with pytest.raises(ValueError, match="startup validation failed"):
        scheduler.main()

    assert calls == [("validate", ["nodeseek"])]
