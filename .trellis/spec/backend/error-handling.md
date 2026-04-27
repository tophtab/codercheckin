# Error Handling

> How errors are handled in this project.

---

## Overview

Error handling in this repository is simple and operational.
Most scripts are daily automation jobs, so the primary goal is:

- fail fast when required configuration is missing
- print enough detail to understand the failure in CI logs
- send a Telegram notification when the script can still do so
- exit with a non-zero status so CI marks the run as failed

This project does not use a shared exception hierarchy across all modules.
Most modules rely on built-in exceptions, return booleans for operation status,
or define small local exception types for narrow integrations.

---

## Error Types

Current patterns in the repository:

- Use `ValueError` for missing required environment variables in executable scripts, as in [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:102) and [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:182).
- Use broad `except Exception as e` blocks at script boundaries to guarantee log output and process failure, as in [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:54).
- Define small custom exception types only when wrapping a third-party API, as in `NetworkException` and `ApiException` in [onepoint3acres/two-captcha/api.py](/home/toph/CloudCheckin/onepoint3acres/two-captcha/api.py:6).

There is no project-wide custom base exception today.

---

## Error Handling Patterns

### Script Entry Boundaries

Wrap the top-level execution flow in `try/except`, print the error, and exit with
status `1`.

Examples:

- [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:100)
- [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:178)

### Helper Functions

Inside helpers, the codebase currently mixes two styles:

- return booleans or `None` values to indicate operational failure
- raise once the caller reaches a point where the whole job should fail

Examples:

- [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:27) returns `(once, signed)` instead of raising for every bad page state.
- [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:109) returns `None, None` when the question cannot be resolved.
- [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:22) exits the process when notification configuration is invalid because the helper is treated as terminal infrastructure.

### Worker Code

Cloudflare Worker code should catch errors and convert them into HTTP responses
with explicit `success` or `error` fields.

Example:

- [cloudflareworkers/src/v2ex.js](/home/toph/CloudCheckin/cloudflareworkers/src/v2ex.js:109) returns a JSON error response with HTTP `500` when the Worker-side flow fails.

---

## API Error Responses

There is no shared Python API server in this repository.

For Worker endpoints, use JSON responses with an explicit success/failure shape.
Current examples include:

- success payloads such as `{ success: true, message: ... }`
- failure payloads such as `{ success: false, error: ..., message: ... }`

Reference: [cloudflareworkers/src/v2ex.js](/home/toph/CloudCheckin/cloudflareworkers/src/v2ex.js:115)

---

## Required Patterns

- Validate required environment variables before doing network work.
- Preserve enough context in error messages to identify which platform and which step failed.
- Use `sys.exit(1)` in Python job entrypoints when the automation cannot complete successfully.
- Send Telegram notifications for failures when notification configuration is already available.

---

## Common Mistakes

- Do not swallow exceptions and continue silently. CI must fail when a platform job fails.
- Do not raise without first recording enough information in stdout or a Telegram message.
- Do not assume notification sending is harmless; [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:22) can itself terminate the process if configuration is incomplete.
- Do not mix success and failure states in the same return value without a clear convention. If a helper returns `None` or `False`, the caller must check it immediately.
