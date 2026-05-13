# Logging Guidelines

> How logging is done in this project.

---

## Overview

The project uses a custom stdout logging helper in `runtime_log.py`, not the
standard `logging` package. Call `runtime_log.log()` for runtime messages so
every line gets a local timestamp and UTC offset.

`format_log_message` prefixes every line of a multiline message. Tests in
`tests/test_runtime_log.py` and `tests/log_assertions.py` verify this behavior.

---

## Log Levels

There are no log levels. Message text carries the event meaning:

- Normal lifecycle messages: "Starting check-in target ...", "Next run
  scheduled at ...", "Startup cookie validation completed".
- Recoverable integration problems: "Cookie Cloud returned invalid JSON",
  "Telegram configuration is incomplete, cannot send notification".
- Failures: "Check-in target 'v2ex' failed with exit code 7", "Scheduled
  check-in failed at ...".

Do not introduce mixed logging styles unless the whole project is migrated.

---

## Structured Logging

Logs are plain text with a timestamp prefix:

```text
2026-05-03 09:08:07 (UTC+08:00) Starting check-in target 'v2ex'
```

Scheduler-facing timestamps include the timezone name when formatting scheduled
times, for example:

```text
2026-04-29 03:30:00 Asia/Shanghai (UTC+08:00)
```

When logging subprocess failure output, preserve stream names with the existing
format from `checkin_runner.py`:

```text
  [stderr] actual error string: cookie expired
```

### Timestamped Runtime Console Logs

Runtime logs must preserve these contracts:

- Emit through `runtime_log.log(...)` unless a test intentionally exercises raw
  stdout/stderr forwarding.
- Use the process-local timezone from `datetime.now().astimezone()`.
- Render `YYYY-MM-DD HH:MM:SS (UTC+08:00) message` when `TZ=Asia/Shanghai`.
- Prefix every line of a multiline message.
- Flush by default so Docker and NAS logs show progress promptly.

Validation cases to preserve:

| Condition | Expected Behavior |
|----------|-------------------|
| `TZ=Asia/Shanghai` | Prefix contains `(UTC+08:00)` |
| Process timezone has a negative offset | Prefix contains `UTC-..:..` with the correct sign |
| Message has multiple lines | Each output line starts with a timestamp prefix |
| Message is an exception object | `str(exception)` appears after the timestamp |
| Runtime code needs a new log | Use `runtime_log.log(...)`, not direct `print(...)` |

---

## What to Log

- Startup cookie validation start, success, and per-target source labels. Log
  only safe source labels such as `environment` or `Cookie Cloud`, not cookie
  values.
- Target start, target success, target failure summaries, and recent captured
  subprocess output for failed targets.
- Scheduler start configuration, next run time, periodic wait status, scheduled
  run start, scheduled run success, and scheduled run failure.
- Attendance account progress, randomized delay, HTTP status code, response
  content, success, failure, and network/process errors.
- Cookie Cloud request/decryption/shape failures and successful client-side
  decryption.
- V2EX authentication markers, unsupported action detection, redeem request
  failures, and balance confirmation results.
- Telegram notification success/failure and missing configuration.

---

## What NOT to Log

- Do not log cookie values from environment variables or Cookie Cloud. Existing
  startup validation tests assert this.
- Do not log V2EX `once` tokens from redeem URLs. Existing V2EX tests assert
  tokens are absent from status messages and captured logs.
- Do not log Telegram bot tokens, chat IDs, Cookie Cloud UUID/password values,
  decrypted payloads, or full request URLs that contain secrets.
- Do not log exception strings when they may include a secret unless a test
  proves the secret is not exposed. V2EX network exception handling logs only
  the exception type for this reason.

## Tests Required

- Unit-test `format_log_timestamp` for positive and negative UTC offsets.
- Unit-test `format_log_message` for single-line and multiline messages.
- Assert runtime call sites produce timestamp-prefixed output with
  `tests.log_assertions.assert_timestamped_lines`.
- Keep substring assertions for operational message content after adding prefix
  assertions.
- For scheduler logs, test startup configuration, next-run timestamps, periodic
  wait status, run boundaries, and failure logs.
