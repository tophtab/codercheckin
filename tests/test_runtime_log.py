import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from runtime_log import format_log_message, format_log_timestamp, log


def test_format_log_timestamp_uses_local_offset_format() -> None:
    timestamp = datetime(2026, 5, 3, 9, 8, 7, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert format_log_timestamp(timestamp) == "2026-05-03 09:08:07 (UTC+08:00)"


def test_format_log_timestamp_uses_process_timezone(monkeypatch) -> None:
    original_tz = os.environ.get("TZ")
    monkeypatch.setenv("TZ", "Asia/Shanghai")
    time.tzset()

    try:
        assert "(UTC+08:00)" in format_log_timestamp()
    finally:
        if original_tz is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = original_tz
        time.tzset()


def test_format_log_timestamp_handles_negative_offsets() -> None:
    timestamp = datetime(2026, 5, 2, 21, 8, 7, tzinfo=ZoneInfo("America/New_York"))

    assert format_log_timestamp(timestamp) == "2026-05-02 21:08:07 (UTC-04:00)"


def test_format_log_message_preserves_message_after_prefix() -> None:
    timestamp = datetime(2026, 5, 3, 9, 8, 7, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert (
        format_log_message("Starting check-in target 'v2ex'", now=timestamp)
        == "2026-05-03 09:08:07 (UTC+08:00) Starting check-in target 'v2ex'"
    )


def test_format_log_message_prefixes_each_multiline_message_line() -> None:
    timestamp = datetime(2026, 5, 3, 9, 8, 7, tzinfo=ZoneInfo("Asia/Shanghai"))

    assert format_log_message("first line\nsecond line", now=timestamp) == (
        "2026-05-03 09:08:07 (UTC+08:00) first line\n"
        "2026-05-03 09:08:07 (UTC+08:00) second line"
    )


def test_log_writes_timestamped_message(capsys) -> None:
    timestamp = datetime(2026, 5, 3, 9, 8, 7, tzinfo=ZoneInfo("Asia/Shanghai"))

    log("Cookie Cloud payload decrypted client-side", now=timestamp)

    assert capsys.readouterr().out == (
        "2026-05-03 09:08:07 (UTC+08:00) "
        "Cookie Cloud payload decrypted client-side\n"
    )
