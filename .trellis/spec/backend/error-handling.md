# Error Handling

> How errors are handled in this project.

---

## Overview

This project is a CLI/background worker. Errors are either converted into a
target exit code, raised with explicit context, or logged and treated as a
recoverable false/empty result when the caller can continue safely.

Entrypoints catch broad exceptions at the process boundary, write the exception
through `runtime_log.log`, and exit non-zero. Internal code should keep errors
typed or contextual enough that the final log line is actionable.

---

## Error Types

- Use `ValueError` for invalid environment configuration and unsupported runtime
  inputs. Examples: empty `CHECKIN_TARGETS`, unknown targets, invalid cron
  expressions, unknown timezones, missing cookies, and unsupported V2EX mission
  actions.
- Use `TargetExecutionError` from `checkin_runner.py` for one target process
  that fails or cannot start. It carries `target`, `returncode`, and recent
  stdout/stderr context.
- Use `MultipleTargetExecutionError` when more than one target fails. It
  subclasses `TargetExecutionError` so callers that only understand target
  failure handling can still catch it.
- Return `False`, `None`, or an empty string for optional integrations that can
  fail without crashing the caller. Examples: Telegram notification delivery and
  Cookie Cloud lookup/decryption.

---

## Error Handling Patterns

- Catch broad exceptions only at process or network boundaries. `run.py`,
  `scheduler.py`, `nodeseek/nodeseek.py`, `deepflood/deepflood.py`, and
  `v2ex/v2ex.py` all catch `Exception` under `if __name__ == "__main__"`, log
  the exception, and exit with code `1`.
- In target orchestration, continue running later targets even if an earlier
  target fails. `run_targets` collects failures, logs recent output, and raises
  one aggregate error after all requested targets have been attempted.
- Wrap subprocess start failures. `_run_target_process` catches `OSError` and
  raises `TargetExecutionError` with `returncode=None` plus recent stderr text.
- For attendance-style platform network failures, notify and return `1` from
  `run_attendance_checkin` instead of raising from the middle of the account
  loop.
- For V2EX, validate action URLs before requesting them. Only normalized
  `https://www.v2ex.com/balance` and
  `https://www.v2ex.com/mission/daily/redeem?once=...` actions are supported.
- For Cookie Cloud, log request/decryption/shape problems and return `None` or
  an empty cookie string. Direct environment cookies remain the preferred source.

### Script Entry Boundaries

Wrap top-level execution in `try/except`, log the error, and exit with status
`1`. Keep this behavior in `run.py`, `scheduler.py`, and platform modules.

### Helper Functions

Inside helpers, prefer one clear convention per helper:

- return booleans or `None` values for recoverable operational failure
- raise once the caller reaches a point where the whole job should fail

Examples:

- `get_daily_mission_action` returns `(action_url, signed, message)` instead of
  raising for every V2EX page state.
- `send_tg_notification` returns `False` for missing Telegram config or delivery
  failure.
- `parse_targets` and `load_schedule_config` raise `ValueError` because invalid
  configuration should stop startup.

### Scheduler Boundary

The scheduler must validate `TZ`, `CHECKIN_CRON`, target names, and safe cookie
availability before entering the wait loop. Missing cookies for enabled targets
should fail before logging the next scheduled run.

---

## API Error Responses

There is no HTTP API. User-visible failures are CLI logs and process exit
codes:

- Success returns `0`.
- Failed platform modules return or exit `1`.
- `run_targets` raises `TargetExecutionError` or
  `MultipleTargetExecutionError`; the outer entrypoint logs the formatted
  message and exits `1`.
- Notification failures are logged but do not turn a successful check-in into a
  failed check-in.

---

## Common Mistakes

- Do not stop the whole multi-target run on the first failed target. Preserve
  the current behavior of trying the remaining targets, then raising a summary.
- Do not log secrets while reporting errors. Tests assert that direct cookies and
  V2EX `once` tokens do not appear in status messages or logs.
- Do not treat an explicit `{"success": false}` response as success just because
  the HTTP status is `200`, unless the message clearly means the account was
  already checked in.
- Do not make optional integrations fatal unless they are required for startup
  validation. Missing Telegram config returns `False`; missing cookies for
  enabled targets raises before the scheduler starts waiting.

## Validation Matrix

| Condition | Expected Behavior |
|----------|-------------------|
| Direct platform cookie is set | Use it immediately and skip Cookie Cloud |
| Direct cookie missing, Cookie Cloud matching domain found | Use Cookie Cloud and log only the safe source label |
| Direct cookie missing and Cookie Cloud has no match | Fail before making platform network requests |
| `CHECKIN_TARGETS` contains unsupported names | Exit non-zero with the supported target list |
| One target subprocess exits non-zero | Log failure, continue with later targets, then raise after all targets run |
| Multiple targets fail | Raise an aggregate error summarizing every failed target |
| Platform reports already checked in | Treat as an idempotent successful run |
| Platform JSON returns explicit `success: false` | Treat as business failure unless the message means already checked in |
| `CHECKIN_CRON` or `TZ` is invalid | Scheduler exits non-zero before waiting |
