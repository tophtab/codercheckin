# Error Handling

> How errors are handled in this project.

---

## Overview

Error handling in this repository is simple and operational.
Most scripts are daily automation jobs, so the primary goal is:

- fail fast when required configuration is missing
- print enough detail to understand the failure in local or container logs
- send a Telegram notification when the script can still do so
- exit with a non-zero status so one-shot runs and scheduled subprocesses mark the run as failed

This project does not use a shared exception hierarchy across all modules.
Most modules rely on built-in exceptions, return booleans for operation status,
or define small local exception types for narrow integrations.

---

## Error Types

Current patterns in the repository:

- Use `ValueError` for missing required environment variables in executable scripts, as in [v2ex/v2ex.py](/home/toph/codercheckin/v2ex/v2ex.py:102) and [run.py](/home/toph/codercheckin/run.py:8).
- Use broad `except Exception as e` blocks at script boundaries to guarantee log output and process failure, as in [nodeseek/nodeseek.py](/home/toph/codercheckin/nodeseek/nodeseek.py:54).
- Use broad `except Exception as e` blocks at script boundaries to guarantee log output and process failure, as in [deepflood/deepflood.py](/home/toph/codercheckin/deepflood/deepflood.py:54).

There is no project-wide custom base exception today.

---

## Error Handling Patterns

### Script Entry Boundaries

Wrap the top-level execution flow in `try/except`, print the error, and exit with
status `1`.

Examples:

- [v2ex/v2ex.py](/home/toph/codercheckin/v2ex/v2ex.py:100)
- [run.py](/home/toph/codercheckin/run.py:6)

### Helper Functions

Inside helpers, the codebase currently mixes two styles:

- return booleans or `None` values to indicate operational failure
- raise once the caller reaches a point where the whole job should fail

Examples:

- [v2ex/v2ex.py](/home/toph/codercheckin/v2ex/v2ex.py:195) returns `(action_url, signed, message)` from daily mission action detection instead of raising for every bad page state.
- [telegram/notify.py](/home/toph/codercheckin/telegram/notify.py:1) returns `False` when notification configuration is invalid or delivery fails, letting the main job decide whether the overall run should fail.

### Scheduler Boundary

The long-running scheduler should validate its own cron/timezone configuration
up front, print the failure, and exit with status `1` if startup cannot proceed.

Example:

- [scheduler.py](/home/toph/codercheckin/scheduler.py:14) raises `ValueError` for invalid `TZ` or `CHECKIN_CRON` configuration and converts that into process failure in the `__main__` block.

---

## API Error Responses

There is no shared Python API server in this repository.

---

## Required Patterns

- Validate required environment variables before doing network work.
- Preserve enough context in error messages to identify which platform and which step failed.
- Use `sys.exit(1)` in Python job entrypoints when the automation cannot complete successfully.
- Send Telegram notifications for failures when notification configuration is already available.
- Keep scheduler startup validation separate from per-platform failure handling.

---

## Common Mistakes

- Do not swallow exceptions and continue silently. The process or scheduled subprocess must fail when a platform job fails.
- Do not raise without first recording enough information in stdout or a Telegram message.
- Do not assume notification sending is harmless; callers should handle the `False` return from [telegram/notify.py](/home/toph/codercheckin/telegram/notify.py:1) when notification delivery matters.
- Do not mix success and failure states in the same return value without a clear convention. If a helper returns `None` or `False`, the caller must check it immediately.
