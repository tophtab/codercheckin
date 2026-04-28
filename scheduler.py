import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from croniter import croniter

from checkin_runner import parse_targets, run_targets


DEFAULT_CRON = "0 3 * * *"
DEFAULT_TIMEZONE = "Asia/Shanghai"


def load_schedule_config() -> tuple[str, str, ZoneInfo]:
    timezone_name = os.environ.get("TZ", DEFAULT_TIMEZONE).strip() or DEFAULT_TIMEZONE
    cron_expression = os.environ.get("CHECKIN_CRON", DEFAULT_CRON).strip() or DEFAULT_CRON

    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as err:
        raise ValueError(f"Unknown timezone: {timezone_name}") from err

    if not croniter.is_valid(cron_expression):
        raise ValueError(f"Invalid CHECKIN_CRON expression: {cron_expression}")

    return cron_expression, timezone_name, timezone


def get_next_run(now: datetime, cron_expression: str) -> datetime:
    return croniter(cron_expression, now).get_next(datetime)


def sleep_until(target_time: datetime) -> None:
    while True:
        seconds_remaining = (target_time - datetime.now(target_time.tzinfo)).total_seconds()
        if seconds_remaining <= 0:
            return
        time.sleep(min(seconds_remaining, 60))


def main() -> int:
    cron_expression, timezone_name, timezone = load_schedule_config()
    targets = parse_targets()

    print(
        "Scheduler started with "
        f"TZ={timezone_name}, CHECKIN_CRON={cron_expression}, "
        f"CHECKIN_TARGETS={','.join(targets)}",
        flush=True,
    )

    while True:
        now = datetime.now(timezone)
        next_run = get_next_run(now, cron_expression)
        print(f"Next run scheduled at {next_run.isoformat()}", flush=True)
        sleep_until(next_run)

        started_at = datetime.now(timezone)
        print(f"Starting scheduled check-in at {started_at.isoformat()}", flush=True)
        exit_code = run_targets(targets)
        finished_at = datetime.now(timezone)

        if exit_code == 0:
            print(f"Scheduled check-in finished at {finished_at.isoformat()}", flush=True)
            continue

        print(
            f"Scheduled check-in failed with exit code {exit_code} at {finished_at.isoformat()}",
            flush=True,
        )


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Scheduler stopped by user", flush=True)
        sys.exit(0)
    except Exception as err:
        print(err, flush=True)
        sys.exit(1)
