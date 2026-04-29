# Logging Guidelines

> How logging is done in this project.

---

## Overview

This project does not use Python's `logging` module or a structured logging
framework. The actual convention today is straightforward console logging:

- Python scripts use `print(..., flush=True)`
- Important outcomes are also pushed to Telegram

The purpose of logging here is operational visibility in local runs, Docker
container logs, and NAS troubleshooting, not analytics or log aggregation.

---

## Log Levels

The repository does not formally implement log levels, but current usage maps to
these practical categories:

- Progress information: plain `print` or `console.log`
- Failure details: `print` with explicit error text
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
- Include timestamps when the event timing matters, as in [scheduler.py](/home/toph/CloudCheckin/scheduler.py:50).

If future work adds a logging library, keep the output simple and compatible with
container logs unless there is a clear operational need for more structure.

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

- Do not add silent failure paths with no `print` or `console` output.
- Do not log secrets just because container logs are private; treat logs as potentially exposed.
- Do not rely only on Telegram for diagnosis. Stdout should still explain the failure.
- Do not introduce a heavy logging framework unless the repository operational model actually requires it.
