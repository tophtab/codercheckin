# Directory Structure

> How backend code is organized in this project.

---

## Overview

This repository is a small automation project, not a layered web backend.
The main backend code is a set of Python entry modules that perform daily
check-in requests against external platforms, plus thin local orchestration
entrypoints for one-shot runs and long-running Docker scheduling.

Write new code to match that shape instead of introducing generic `src/`,
controller/service/repository, or ORM-based layouts that do not exist here.

---

## Directory Layout

```text
.
|-- deepflood/
|   |-- __init__.py
|   +-- deepflood.py
|-- nodeseek/
|   |-- __init__.py
|   +-- nodeseek.py
|-- telegram/
|   |-- __init__.py
|   +-- notify.py
|-- v2ex/
|   |-- __init__.py
|   +-- v2ex.py
|-- cookiecloud/
|   |-- __init__.py
|   +-- client.py
|-- Dockerfile
|-- docker-compose.yml
|-- docker-compose.build.yml
|-- checkin_runner.py
|-- attendance_checkin.py
|-- run.py
|-- scheduler.py
|-- requirements.txt
|-- README.md
```

---

## Module Organization

Each platform gets its own top-level package.

- Keep one package per platform, for example [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:1), [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:1), and [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:1).
- Put platform-specific request headers, endpoint URLs, parsing logic, and message formatting inside that platform package.
- Put shared notification behavior in [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1) rather than re-implementing Telegram calls in each platform module.
- Put cross-platform integrations in a small top-level helper package when multiple platform scripts need the same behavior, as in [cookiecloud/client.py](/home/toph/CloudCheckin/cookiecloud/client.py:1).
- Put shared platform execution behavior in small top-level helpers when two or more platform modules genuinely use the same flow, as in [attendance_checkin.py](/home/toph/CloudCheckin/attendance_checkin.py:1) for NodeSeek and DeepFlood attendance requests.

For Python scripts, the package module is both library code and CLI entrypoint.
The usual pattern is helper functions or configuration at module scope, a
`main() -> int` function that validates environment variables and executes the
workflow, then an `if __name__ == "__main__":` block that converts exceptions
into process exit codes. Importing a platform module should not perform cookie
lookup or external network work.

Examples:

- [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:1) defines helpers first and executes the flow from `main()`.
- [attendance_checkin.py](/home/toph/CloudCheckin/attendance_checkin.py:1) holds the shared attendance flow used by platform modules whose behavior only differs by endpoint, domains, and labels.
- [run.py](/home/toph/CloudCheckin/run.py:1) is the one-shot batch entrypoint and shells out to existing module entrypoints instead of re-implementing their flows.
- [scheduler.py](/home/toph/CloudCheckin/scheduler.py:1) is the long-running Docker/NAS scheduler entrypoint that triggers batch runs from `CHECKIN_CRON`.
- [checkin_runner.py](/home/toph/CloudCheckin/checkin_runner.py:1) holds the shared target parsing and subprocess execution logic used by both entrypoints.

---

## Naming Conventions

- Use lowercase directory names for platforms: `v2ex`, `nodeseek`, `deepflood`, `telegram`.
- Keep the main module name the same as the package name when the package has a single executable entrypoint, for example `v2ex/v2ex.py`.
- Use `snake_case` for Python functions and variables.
- Use `UPPER_SNAKE_CASE` for environment variable names such as `V2EX_COOKIE`, `NODESEEK_COOKIE`, `DEEPFLOOD_COOKIE`, and `TELEGRAM_TOKEN`.
- Keep shared constant maps simple and explicit, for example the `MODULES` dict in [checkin_runner.py](/home/toph/CloudCheckin/checkin_runner.py:6).

---

## Patterns To Follow

- Load local environment variables near module startup with `load_dotenv()` for Python scripts that run locally.
- Keep per-platform request headers close to the code that uses them.
- Import the shared notification helper rather than duplicating outbound Telegram code.
- Use `python -m <package>.<module>` as the expected local execution path, matching the commands documented in [README.md](/home/toph/CloudCheckin/README.md:155).
- For Docker or NAS execution, keep the entrypoint thin and delegate to the existing `python -m ...` commands, as in [checkin_runner.py](/home/toph/CloudCheckin/checkin_runner.py:1).
- Keep long-running schedule concerns in [scheduler.py](/home/toph/CloudCheckin/scheduler.py:1) instead of embedding sleep/cron loops into each platform module.

---

## Forbidden Patterns

- Do not introduce a fake `src/` or web-service layering model unless the repository architecture actually changes.
- Do not place secrets or local cookies in tracked files. This project expects secrets from environment variables only.
- Do not duplicate the Telegram HTTP client in each platform script when [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1) already exists.
- Do not make the Docker batch runner import platform modules directly just to execute them. Platform modules should be import-safe, but the runner should still execute their CLI entrypoints as subprocesses so local `python -m ...` behavior matches Docker/NAS behavior.
- Do not fold scheduler behavior into `run.py` if that would blur the difference between one-shot execution and long-running container orchestration.

---

## Examples

- Platform package with module entrypoint: [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:1)
- Shared attendance helper: [attendance_checkin.py](/home/toph/CloudCheckin/attendance_checkin.py:1)
- Shared notification helper: [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1)
- One-shot batch entrypoint: [run.py](/home/toph/CloudCheckin/run.py:1)
- Long-running scheduler entrypoint: [scheduler.py](/home/toph/CloudCheckin/scheduler.py:1)
