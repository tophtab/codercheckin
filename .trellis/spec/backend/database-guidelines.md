# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

The current project has no database, ORM, migrations, or persistent storage
layer. Runtime state comes from environment variables, Cookie Cloud responses,
HTTP responses from target sites, and in-memory process state.

Do not add a database abstraction for normal check-in behavior. Prefer
stateless functions and explicit inputs so the tool remains simple to run in
Docker and NAS deployments.

## Current Storage Model

- Runtime secrets live in environment variables.
- Static platform metadata lives in Python modules such as `checkin_runner.py`
  and the platform packages.
- Remote platforms remain the source of truth for check-in state, daily rewards,
  and balances.
- Docker Compose and the scheduler provide orchestration, not durable
  application storage.

If a feature needs to remember state between runs, first check whether the
remote platform already exposes enough information to avoid local persistence.

---

## Query Patterns

There are no database queries. Remote data access is performed through HTTP:

- `cookiecloud/client.py` fetches Cookie Cloud payloads with `requests.get` and
  falls back to `requests.post` with a password body.
- `attendance_checkin.py` posts attendance requests with `curl_cffi.requests`
  and browser impersonation.
- `v2ex/v2ex.py` fetches mission and balance pages, using a shared session when
  cookies must be preserved between requests.

All outbound requests should use `REQUEST_TIMEOUT_SECONDS` from `config.py`.

Examples:

- `v2ex/v2ex.py` confirms daily mission success from `/balance` instead of a
  local record.
- `cookiecloud/client.py` fetches remote JSON, normalizes or decrypts it, and
  keeps only an in-process cache.
- `scheduler.py` coordinates when modules run but does not persist schedule
  state.

---

## Migrations

There are no migrations. If future work introduces persistent storage, it must
also introduce explicit migration tooling, tests, and deployment instructions.
Until then, do not create ad hoc local files as hidden state.

---

## Naming Conventions

Not applicable for tables or columns. Existing configuration names are
environment variable oriented:

- Target cookie variables use uppercase service names plus `_COOKIE`, such as
  `NODESEEK_COOKIE`, `DEEPFLOOD_COOKIE`, and `V2EX_COOKIE`.
- Shared runtime controls use uppercase names such as `CHECKIN_TARGETS`,
  `CHECKIN_CRON`, `TZ`, `COOKIE_CLOUD_URL`, `COOKIE_CLOUD_UUID`, and
  `COOKIE_CLOUD_PASSWORD`.

---

## Common Mistakes

- Do not introduce persistent state to remember whether a target has checked in.
  The current pattern asks the target site or confirmation page and treats
  "already checked in" responses as success.
- Do not cache Cookie Cloud data outside the process. `cookiecloud/client.py`
  uses in-memory module globals only to avoid repeated fetches during one run.
- Do not store cookies, Telegram tokens, or decrypted Cookie Cloud payloads in
  repository files or logs.
