# Directory Structure

> How backend code is organized in this project.

---

## Overview

This repository is a small automation project, not a layered web backend.
The main backend code is a set of Python entry modules that perform daily
check-in requests against external platforms, plus a small Cloudflare Worker
used as a scheduler/webhook trigger.

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
|-- onepoint3acres/
|   |-- __init__.py
|   |-- onepoint3acres.py
|   |-- questions.py
|   +-- two-captcha/
|       |-- api.py
|       +-- two-captcha.py
|-- telegram/
|   |-- __init__.py
|   +-- notify.py
|-- v2ex/
|   |-- __init__.py
|   +-- v2ex.py
|-- cloudflareworkers/
|   |-- src/
|   |   |-- nodeseek.js
|   |   +-- v2ex.js
|   |-- README.md
|   +-- wrangler*.toml
|-- cookiecloud/
|   |-- __init__.py
|   +-- client.py
|-- Dockerfile
|-- worker.js
|-- docker-compose.yml
|-- docker-compose.build.yml
|-- run.py
|-- requirements.txt
|-- README.md
```

---

## Module Organization

Each platform gets its own top-level package.

- Keep one package per platform, for example [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:1), [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:1), and [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:1).
- Put platform-specific request headers, endpoint URLs, parsing logic, and message formatting inside that platform package.
- Put shared notification behavior in [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1) rather than re-implementing Telegram calls in each platform module.
- Keep static lookup data beside the feature that uses it, as in [onepoint3acres/questions.py](/home/toph/CloudCheckin/onepoint3acres/questions.py:1).
- Keep third-party integration helpers near the feature that depends on them when they are not broadly reused, as in [onepoint3acres/two-captcha/api.py](/home/toph/CloudCheckin/onepoint3acres/two-captcha/api.py:1).
- Put cross-platform integrations in a small top-level helper package when multiple platform scripts need the same behavior, as in [cookiecloud/client.py](/home/toph/CloudCheckin/cookiecloud/client.py:1).

For Python scripts, the package module is both library code and CLI entrypoint.
The usual pattern is helper functions or a small class at module scope, then an
`if __name__ == "__main__":` block that validates environment variables and
executes the workflow.

Examples:

- [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:27) defines helpers first and executes the flow in the `__main__` block.
- [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:14) wraps platform logic in a class because the flow needs shared session state.
- [worker.js](/home/toph/CloudCheckin/worker.js:1) and [cloudflareworkers/src/v2ex.js](/home/toph/CloudCheckin/cloudflareworkers/src/v2ex.js:1) keep Worker code separate from Python automation code.
- [run.py](/home/toph/CloudCheckin/run.py:1) is the batch container entrypoint and shells out to existing module entrypoints instead of re-implementing their flows.

---

## Naming Conventions

- Use lowercase directory names for platforms: `v2ex`, `nodeseek`, `deepflood`, `telegram`.
- Keep the main module name the same as the package name when the package has a single executable entrypoint, for example `v2ex/v2ex.py`.
- Use `snake_case` for Python functions and variables.
- Use `UPPER_SNAKE_CASE` for environment variable names such as `V2EX_COOKIE`, `NODESEEK_COOKIE`, `TWOCAPTCHA_APIKEY`, and `TELEGRAM_TOKEN`.
- Keep data-only files simple and explicit, for example the `questions` dict in [onepoint3acres/questions.py](/home/toph/CloudCheckin/onepoint3acres/questions.py:1).

---

## Patterns To Follow

- Load local environment variables near module startup with `load_dotenv()` for Python scripts that run locally or in CI.
- Keep per-platform request headers close to the code that uses them.
- Import the shared notification helper rather than duplicating outbound Telegram code.
- Use `python -m <package>.<module>` as the expected local execution path, matching the commands documented in [README.md](/home/toph/CloudCheckin/README.md:153).
- For Docker or NAS batch execution, keep the container entrypoint thin and delegate to the existing `python -m ...` commands, as in [run.py](/home/toph/CloudCheckin/run.py:35).

---

## Forbidden Patterns

- Do not introduce a fake `src/` or web-service layering model unless the repository architecture actually changes.
- Do not place secrets or local cookies in tracked files. This project expects secrets from environment variables only.
- Do not duplicate the Telegram HTTP client in each platform script when [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1) already exists.
- Do not mix Cloudflare Worker code into Python packages. Keep Worker-specific logic in `worker.js` or `cloudflareworkers/src/`.
- Do not make the Docker batch runner import platform modules directly just to execute them. Some modules validate configuration at import time, so the runner should execute their CLI entrypoints as subprocesses.

---

## Examples

- Platform package with module entrypoint: [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:1)
- Shared notification helper: [telegram/notify.py](/home/toph/CloudCheckin/telegram/notify.py:1)
- Stateful class-based flow for a more complex platform: [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:14)
- Worker-side scheduler trigger: [worker.js](/home/toph/CloudCheckin/worker.js:1)
