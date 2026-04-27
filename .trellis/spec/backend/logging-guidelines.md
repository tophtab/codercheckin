# Logging Guidelines

> How logging is done in this project.

---

## Overview

This project does not use Python's `logging` module or a structured logging
framework. The actual convention today is straightforward console logging:

- Python scripts use `print(..., flush=True)`
- Cloudflare Workers use `console.log(...)` and `console.error(...)`
- Important outcomes are also pushed to Telegram

The purpose of logging here is operational visibility in CI and Worker logs,
not analytics or log aggregation.

---

## Log Levels

The repository does not formally implement log levels, but current usage maps to
these practical categories:

- Progress information: plain `print` or `console.log`
- Failure details: `print` with explicit error text or `console.error`
- User-visible completion/failure notices: Telegram notifications

Examples:

- Progress logs in [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:29) announce account index, delay, status code, and response text.
- Worker progress logs in [worker.js](/home/toph/CloudCheckin/worker.js:12) record scheduled execution time and response status.
- Error logs in [worker.js](/home/toph/CloudCheckin/worker.js:20) and [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:46) print explicit failure messages.

---

## Structured Logging

There is no formal structured logging format.

Current conventions to preserve:

- Include platform or workflow context directly in the message text.
- Include response status or parsed outcome when it is useful for debugging.
- Flush Python output immediately in CI-facing scripts.
- For Worker logs, include timestamps when the event timing matters, as in [worker.js](/home/toph/CloudCheckin/worker.js:11).

If future work adds a logging library, keep the output simple and compatible with
CI logs unless there is a clear operational need for more structure.

---

## What To Log

- Start and end of a platform check-in flow.
- Which account is being processed when a script supports multiple cookies.
- External HTTP status codes and short response details when a request fails.
- Parsing failures, missing environment variables, or third-party captcha issues.
- Final success or failure messages that explain the outcome.

Examples:

- [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:31) logs account selection and randomized delay.
- [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:42) logs status code and response content.
- [cloudflareworkers/src/v2ex.js](/home/toph/CloudCheckin/cloudflareworkers/src/v2ex.js:147) logs why cookie validation or parsing failed.

---

## What NOT To Log

- Full cookies or tokens from environment variables.
- Raw secret values such as `TELEGRAM_TOKEN`, `TWOCAPTCHA_APIKEY`, or webhook URLs.
- Full request headers when they include authentication data.
- Excessively noisy HTML payloads unless debugging a parsing breakage locally.

The current code already shows one safe pattern: log cookie presence or length,
not the cookie value itself, as in [cloudflareworkers/src/v2ex.js](/home/toph/CloudCheckin/cloudflareworkers/src/v2ex.js:57).

---

## Common Mistakes

- Do not add silent failure paths with no `print` or `console` output.
- Do not log secrets just because CI logs are private; treat logs as potentially exposed.
- Do not rely only on Telegram for diagnosis. The stdout or Worker log should still explain the failure.
- Do not introduce a heavy logging framework unless the repository operational model actually requires it.
