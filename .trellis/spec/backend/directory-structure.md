# Directory Structure

> How backend code is organized in this project.

---

## Overview

codercheckin is a flat Python application, not a `src/` layout project. Root
modules hold orchestration, shared config, response parsing, scheduling, and
logging. Small packages hold platform-specific check-in code and external
service clients.

There is no web API layer. The runnable entrypoints are command-line modules:
`run.py` runs enabled targets once, `scheduler.py` runs targets on a cron
schedule, and each platform package can be executed with `python -m`.

---

## Directory Layout

```
.
├── attendance_checkin.py      # shared check-in flow for attendance-style sites
├── checkin_response.py        # response success/already-signed detection
├── checkin_runner.py          # target selection, cookie validation, subprocess execution
├── config.py                  # shared constants and environment helpers
├── runtime_log.py             # timestamped stdout logging helper
├── run.py                     # one-shot check-in entrypoint
├── scheduler.py               # cron scheduler entrypoint
├── cookiecloud/               # Cookie Cloud client and cookie resolution
├── deepflood/                 # Deepflood platform module
├── nodeseek/                  # Nodeseek platform module
├── telegram/                  # Telegram notification helper
├── v2ex/                      # V2EX platform module
└── tests/                     # pytest tests and local test helpers
```

---

## Module Organization

- Put shared constants and simple environment access in `config.py`. Existing
  examples include `REQUEST_TIMEOUT_SECONDS`, browser identity constants, and
  `get_env_required`.
- Put reusable platform check-in behavior in root-level helpers. For example,
  `attendance_checkin.py` defines `AttendanceConfig` and
  `run_attendance_checkin`, which are used by both `nodeseek/nodeseek.py` and
  `deepflood/deepflood.py`.
- Keep platform wrappers thin when they fit the shared flow. `nodeseek` and
  `deepflood` define a module-level `CONFIG`, call `load_dotenv()` in `main()`,
  and return the result of `run_attendance_checkin`.
- Use a dedicated package when a platform needs custom parsing or request state.
  `v2ex/v2ex.py` keeps V2EX-specific HTML parsing, URL validation, session
  handling, and balance confirmation together.
- Keep external service integrations in their own package. `cookiecloud/client.py`
  owns Cookie Cloud fetch/decrypt/merge behavior, and `telegram/notify.py` owns
  Telegram notification delivery.
- Keep process orchestration in `checkin_runner.py`. Do not duplicate target
  parsing, startup cookie validation, or subprocess handling in platform modules.
- For Python scripts, keep the common entrypoint shape: helper functions and
  configuration first, `main() -> int`, then an `if __name__ == "__main__":`
  block that converts exceptions into process exit codes.
- Importing platform modules must not perform cookie lookup, network calls,
  sleeps, or Telegram sends. Tests rely on import-safe platform modules.

---

## Naming Conventions

- Module and package names use lowercase snake_case or existing service names:
  `checkin_runner.py`, `runtime_log.py`, `cookiecloud`, `nodeseek`.
- Public orchestration functions use imperative names such as `parse_targets`,
  `validate_target_cookies`, `run_targets`, and `send_tg_notification`.
- Internal helpers are prefixed with `_`, as in `_fetch_cookiecloud_payload`,
  `_normalize_v2ex_action_url`, and `_format_failure_message`.
- Configuration dataclasses are frozen when they describe static target data:
  `AttendanceConfig` and `TargetConfig` are both declared with
  `@dataclass(frozen=True)`.
- Module-level constants are uppercase and centralized near the top of the file:
  `TARGETS`, `DEFAULT_CRON`, `MISSION_DAILY_URL`, and
  `REQUEST_TIMEOUT_SECONDS`.

---

## Examples

- `attendance_checkin.py` + `nodeseek/nodeseek.py` + `deepflood/deepflood.py`
  show the preferred shared-flow pattern for similar attendance APIs.
- `checkin_runner.py` is the reference for target registry shape, environment
  target parsing, startup validation, subprocess isolation, and aggregate
  failure handling.
- `cookiecloud/client.py` is the reference for resolving direct environment
  cookies before falling back to Cookie Cloud.
- `v2ex/v2ex.py` is the reference for a custom platform module that needs
  request sessions, constrained action URL parsing, and post-action
  confirmation.

## Forbidden Patterns

- Do not introduce a `src/` directory, controller/service/repository layering,
  or ORM-style package layout unless the repository architecture actually
  changes.
- Do not place secrets or local cookies in tracked files. This project expects
  secrets from environment variables or Cookie Cloud.
- Do not duplicate Telegram HTTP calls in platform modules when
  `telegram/notify.py` already owns notification delivery.
- Do not make the batch runner import platform modules directly just to execute
  them. `checkin_runner.py` intentionally runs module entrypoints as
  subprocesses so local `python -m ...` behavior matches Docker/NAS behavior.
- Do not fold scheduler behavior into `run.py`; keep one-shot execution and
  long-running container scheduling separate.
