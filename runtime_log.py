from datetime import datetime
from typing import TextIO


def format_log_timestamp(value: datetime | None = None) -> str:
    current_time = value or datetime.now().astimezone()
    if current_time.tzinfo is None:
        current_time = current_time.astimezone()

    offset = current_time.utcoffset()
    if offset is None:
        offset_text = "UTC+00:00"
    else:
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        total_minutes = abs(total_minutes)
        offset_hours, offset_minutes = divmod(total_minutes, 60)
        offset_text = f"UTC{sign}{offset_hours:02d}:{offset_minutes:02d}"

    return f"{current_time.strftime('%Y-%m-%d %H:%M:%S')} ({offset_text})"


def format_log_message(message: object = "", *, now: datetime | None = None) -> str:
    prefix = f"{format_log_timestamp(now)} "
    text = str(message)
    if not text:
        return prefix.rstrip()

    return "".join(f"{prefix}{line}" for line in text.splitlines(keepends=True))


def log(
    message: object = "",
    *,
    flush: bool = True,
    file: TextIO | None = None,
    now: datetime | None = None,
) -> None:
    print(format_log_message(message, now=now), flush=flush, file=file)
