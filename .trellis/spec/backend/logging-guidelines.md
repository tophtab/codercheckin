# Logging Guidelines

> How logging is done in this project.

---

## Overview

This project does not use Python's `logging` module or a structured logging
framework. The actual convention today is timestamped console logging:

- Python scripts use `runtime_log.log(...)`
- `runtime_log.log(...)` prefixes every runtime log line with local process time
  in `YYYY-MM-DD HH:MM:SS (UTC+08:00) message` form when `TZ=Asia/Shanghai`
- Important outcomes are also pushed to Telegram

The purpose of logging here is operational visibility in local runs, Docker
container logs, and NAS troubleshooting, not analytics or log aggregation.

---

## Log Levels

The repository does not formally implement log levels, but current usage maps to
these practical categories:

- Progress information: `runtime_log.log(...)` or `console.log`
- Failure details: `runtime_log.log(...)` with explicit error text
- User-visible completion/failure notices: Telegram notifications

Examples:

- Progress logs in [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:29) announce account index, delay, status code, and response text.
- Scheduler progress logs in [scheduler.py](/home/toph/CloudCheckin/scheduler.py:41) record the cron configuration, next run, and run boundaries.
- Error logs in [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1) and platform scripts print explicit failure messages.

### Scheduler Wait Visibility

Long-running scheduler sleeps must not be silent for the whole wait window.
After logging the next scheduled execution time, `scheduler.py` should also emit
periodic wait-status logs with the target timestamp and remaining duration. This
prevents Docker/NAS operators from mistaking a healthy wait state for a stalled
container when the next cron run is many hours away.

---

## Structured Logging

There is no formal structured logging format.

Current conventions to preserve:

- Include platform or workflow context directly in the message text.
- Include response status or parsed outcome when it is useful for debugging.
- Flush Python output immediately in script and container output.
- Use the process/local timezone for the log prefix; do not hard-code a timezone
  offset in call sites.
- Preserve the existing message text after the timestamp prefix.
- Include timestamps when the event timing matters, as in [scheduler.py](/home/toph/CloudCheckin/scheduler.py:50).

If future work adds a logging library, keep the output simple and compatible with
container logs unless there is a clear operational need for more structure.

---

## Scenario: Timestamped Runtime Console Logs

### 1. Scope / Trigger

- Trigger: adding or changing Python runtime logs, especially scheduler, runner,
  Cookie Cloud, Telegram, or platform module output that appears in Docker/NAS
  logs.

### 2. Signatures

- `runtime_log.format_log_timestamp(value: datetime | None = None) -> str`
- `runtime_log.format_log_message(message: object = "", *, now: datetime | None = None) -> str`
- `runtime_log.log(message: object = "", *, flush: bool = True, file: TextIO | None = None, now: datetime | None = None) -> None`

### 3. Contracts

- Runtime logs must be emitted through `runtime_log.log(...)` unless a test is
  intentionally exercising Python's raw stdout/stderr behavior.
- The timestamp prefix must use the process-local timezone from
  `datetime.now().astimezone()` and render as
  `YYYY-MM-DD HH:MM:SS (UTC+08:00) message` when `TZ=Asia/Shanghai`.
- Message text must stay intact after the prefix so existing operational log
  searches still work.
- Multi-line messages must receive a timestamp prefix on every non-empty output
  line.
- Log calls must flush by default so Docker and NAS log viewers show progress
  promptly.

### 4. Validation & Error Matrix

| Condition | Expected Behavior |
|----------|-------------------|
| `TZ=Asia/Shanghai` | Prefix contains `(UTC+08:00)` |
| Process timezone has a negative offset | Prefix contains `UTC-..:..` with the correct sign |
| Message has multiple lines | Each output line starts with a timestamp prefix |
| Message is an exception object | Log text is `str(exception)` after the timestamp |
| Runtime code needs a new progress or failure log | Use `runtime_log.log(...)`, not direct `print(..., flush=True)` |

### 5. Good / Base / Bad Cases

- Good: `log("Startup cookie validation completed")` emits
  `2026-05-03 07:17:00 (UTC+08:00) Startup cookie validation completed`.
- Base: `log(err)` preserves the exception message after the timestamp without
  logging secrets.
- Bad: `print("Startup validation failed", flush=True)` emits a Docker log line
  with no application timestamp and makes restart timelines harder to diagnose.

### 6. Tests Required

- Unit-test `format_log_timestamp(...)` for positive and negative UTC offsets.
- Unit-test `format_log_message(...)` for single-line and multi-line messages.
- Assert affected runtime call sites produce timestamp-prefixed output, using a
  shared test helper instead of repeating the regex in every test file.
- Keep existing substring assertions for operational message content after
  adding prefix assertions.

### 7. Wrong vs Correct

#### Wrong

```python
print("Cookie Cloud payload decrypted client-side", flush=True)
```

#### Correct

```python
from runtime_log import log

log("Cookie Cloud payload decrypted client-side")
```

---

## What To Log

- Start and end of a platform check-in flow.
- In the batch runner, start and success/failure for each configured target
  before moving to the next target or returning a failure code.
- When a batch runner target subprocess fails, include a bounded recent
  stdout/stderr tail so container logs show the failed step and error string.
- Which account is being processed when a script supports multiple cookies.
- External HTTP status codes and short response details when a request fails.
- Parsing failures, missing environment variables, or third-party captcha issues.
- Final success or failure messages that explain the outcome.
- Scheduler startup configuration and next scheduled execution time.
- Periodic scheduler wait status when the next execution is still in the future.

Examples:

- [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:31) logs account selection and randomized delay.
- [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:42) logs status code and response content.
- [scheduler.py](/home/toph/CloudCheckin/scheduler.py:41) logs scheduler startup and next-run timestamps.

---

## What NOT To Log

- Full cookies or tokens from environment variables.
- Raw secret values such as `TELEGRAM_TOKEN`, `COOKIE_CLOUD_PASSWORD`, or full cookie strings.
- Full request headers when they include authentication data.
- Excessively noisy HTML payloads unless debugging a parsing breakage locally.

---

## Common Mistakes

- Do not add silent failure paths with no `runtime_log.log(...)` or `console`
  output.
- Do not add new direct `print(..., flush=True)` runtime logs in Python modules;
  use `runtime_log.log(...)` so Docker/NAS output keeps a consistent timestamp
  prefix.
- Do not log secrets just because container logs are private; treat logs as potentially exposed.
- Do not rely only on Telegram for diagnosis. Stdout should still explain the failure.
- Do not introduce a heavy logging framework unless the repository operational model actually requires it.
