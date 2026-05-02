# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

This repository is a lightweight automation project. Quality here means:

- the scripts continue to match each platform's real behavior
- secrets stay in environment variables
- failures are obvious in local and container logs
- shared logic is reused instead of cloned carelessly
- local debug commands from the README still work

The codebase is pragmatic rather than heavily abstracted. Follow existing shapes
unless there is a clear maintenance problem to solve.

---

## Forbidden Patterns

- Do not hardcode cookies, tokens, or chat IDs in source files.
- Do not switch a new HTTP flow back to `requests` when the project already prefers `curl_cffi` for sites with stronger anti-bot checks. This preference is documented in [README.md](/home/toph/CloudCheckin/README.md:188).
- Do not duplicate Telegram notification logic in platform scripts.
- Do not ignore return values such as `False`, `None`, or missing parsed data from helper functions.
- Do not introduce large architectural abstractions for one-off platform logic unless multiple modules genuinely need them.

---

## Required Patterns

- Load environment variables with `load_dotenv()` in Python modules that are expected to run locally.
- Validate required configuration before attempting network calls.
- Keep platform-specific constants, endpoints, and headers close to the code that uses them.
- Keep platform modules import-safe: cookie lookup and network requests belong in `main()` or injected helpers, not at module import time.
- Exit with a non-zero code when a scheduled task fails.
- Reuse existing helpers and data modules before adding new utility code.

Examples:

- Shared Telegram helper reuse in [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:6), [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:7), and [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:7).
- Shared attendance request reuse in [attendance_checkin.py](/home/toph/CloudCheckin/attendance_checkin.py:1), with platform-specific configuration kept in [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:1) and [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:1).
- Environment validation in [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:102).
- Local debug execution commands in [README.md](/home/toph/CloudCheckin/README.md:153).

## Scenario: Docker scheduler, runner, and Cookie Cloud fallback

### 1. Scope / Trigger

- Trigger: changing Docker deployment files, batch or scheduler entrypoints, or the way platform cookies are resolved from environment variables.

### 2. Signatures

- One-shot batch entrypoint command: `python run.py`
- Long-running scheduler entrypoint command: `python scheduler.py`
- Batch target selector env: `CHECKIN_TARGETS=nodeseek,deepflood,v2ex`
- Batch target runner signature: `run_targets(targets: list[str]) -> int`
- Startup cookie validation signature: `validate_target_cookies(targets: list[str]) -> None`
- Scheduler timezone env: `TZ=Asia/Shanghai`
- Scheduler cron env: `CHECKIN_CRON=30 3 * * *`
- Deployment image env: `CLOUDCHECKIN_IMAGE=tophtab/cloudcheckin:latest`
- Shared resolver signature: `get_cookie_value(env_name: str, domains: list[str]) -> str`
- Shared attendance signature: `run_attendance_checkin(config: AttendanceConfig, *, get_cookie, notify, sleep, randint, post, timeout) -> int`
- Cookie Cloud endpoint shape: `POST <COOKIE_CLOUD_URL>/get/<COOKIE_CLOUD_UUID>?crypto_type=...`
- Docker Hub publish workflow: `.github/workflows/dockerhub-publish.yml`
- Deployment compose file: `docker-compose.yml`
- Local build override file: `docker-compose.build.yml`

### 3. Contracts

- Direct platform environment variables remain first priority:
  `NODESEEK_COOKIE`, `DEEPFLOOD_COOKIE`, `V2EX_COOKIE`
- `docker-compose.yml` is the deployment contract and must pull by `image` only.
- Local source builds belong in `docker-compose.build.yml`, not in the deployment file.
- Docker Compose is the primary NAS deployment contract and should run the long-lived scheduler by default.
- Cookie Cloud is optional and only used when the direct platform variable is empty.
- Cookie Cloud configuration uses environment variables only:
  `COOKIE_CLOUD_URL`, `COOKIE_CLOUD_UUID`, `COOKIE_CLOUD_PASSWORD`, `COOKIE_CLOUD_CRYPTO_TYPE`
- The shared resolver returns a request-ready cookie header string in `name=value; name2=value2` form.
- The scheduler must validate cookie availability for every configured
  `CHECKIN_TARGETS` target before entering the wait loop.
- Startup validation may accept a non-empty direct platform cookie or a matching
  Cookie Cloud cookie, but it must not print the cookie value, token, password,
  or full request headers.
- If no direct cookie exists and Cookie Cloud cannot provide a matching domain cookie, the platform script must still fail fast before making network requests.
- Platform modules must be safe to import in tests: importing `nodeseek.nodeseek`, `deepflood.deepflood`, or `v2ex.v2ex` must not read cookies or call external services.
- External requests must set a finite timeout so NAS scheduler subprocesses cannot hang indefinitely on one platform.
- `CHECKIN_CRON` must be a valid 5-field cron expression.
- `TZ` must be a valid IANA timezone name accepted by `zoneinfo`.
- `run_targets()` must execute configured targets in order, print each target's
  start and success/failure result, stop at the first non-zero subprocess exit,
  and raise an exception that names the failing target and includes a bounded
  recent stdout/stderr summary.
- `run_targets()` must also wrap subprocess start failures with the failing
  target/module context and a bounded recent output summary, then stop before
  later targets run.
- `run_targets()` must forward target subprocess stdout/stderr while the target
  runs and, on failure, print a bounded recent stdout/stderr summary without
  introducing new secret sources beyond the subprocess output itself.
- Docker Hub publishing uses GitHub repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`.
- Optional GitHub repository variable `DOCKERHUB_IMAGE` overrides the default image name.
- If `DOCKERHUB_IMAGE` is empty, the workflow publishes to `<DOCKERHUB_USERNAME>/cloudcheckin`.
- The publish workflow runs automatically on pushes to `main`, pushes of `v*` git tags, and manual dispatch.

### 4. Validation & Error Matrix

| Condition | Expected Behavior |
|----------|-------------------|
| Direct platform cookie is set | Use it immediately and skip Cookie Cloud |
| Direct platform cookie missing, Cookie Cloud configured, matching domain found | Use Cookie Cloud cookie and print a safe success hint |
| Direct platform cookie missing, Cookie Cloud not configured | Return empty string and let the platform entrypoint raise `ValueError` |
| Cookie Cloud request fails or returns bad JSON | Print a safe error, return empty string, and let the platform entrypoint fail fast |
| Scheduler startup target has direct cookie or Cookie Cloud match | Log the safe cookie source and continue to scheduling |
| Scheduler startup target has no direct cookie and no Cookie Cloud match | Exit non-zero before logging the next scheduled run |
| `CHECKIN_TARGETS` contains unsupported names | `run.py` exits non-zero with the supported target list |
| A check-in target subprocess exits non-zero | `run_targets()` logs the target failure, raises an exception with the failing target and recent stdout/stderr text, and does not run later targets |
| A check-in target subprocess cannot start | `run_targets()` raises a target-specific exception that preserves the module/startup error text and does not run later targets |
| Platform reports "already checked in" | Treat as a successful, idempotent run instead of failing the batch |
| Platform JSON returns `success: false` | Treat as a business failure even if HTTP status is `200`, unless the message is an idempotent already-checked-in response |
| Platform module is imported by tests or tooling | Import succeeds without cookie lookup, sleeps, HTTP requests, or Telegram sends |
| `CHECKIN_CRON` is invalid | `scheduler.py` exits non-zero before entering the loop |
| `TZ` is invalid | `scheduler.py` exits non-zero before entering the loop |
| Server runs `docker compose` with default files | Compose pulls `CLOUDCHECKIN_IMAGE` instead of building locally |
| Local developer needs to build current source | Compose uses `docker-compose.build.yml` as an explicit override |
| Docker Hub username/token missing | Workflow fails in login or image resolution before build/push |
| `DOCKERHUB_IMAGE` contains uppercase letters | Workflow lowercases the final image name before metadata/build |

### 5. Good / Base / Bad Cases

- Good: `V2EX_COOKIE` is set explicitly, so [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:11) uses it without any Cookie Cloud dependency.
- Base: `NODESEEK_COOKIE` is empty, Cookie Cloud is configured, and [cookiecloud/client.py](/home/toph/CloudCheckin/cookiecloud/client.py:20) builds the cookie header from the matched domain payload.
- Bad: `V2EX_COOKIE` is empty and Cookie Cloud has no matching `v2ex.com` cookie, so [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:102) raises before the sign-in flow starts.
- Good: [scheduler.py](/home/toph/CloudCheckin/scheduler.py:1) starts with `TZ=Asia/Shanghai` and `CHECKIN_CRON=30 3 * * *`, logs the next run, and then delegates to [checkin_runner.py](/home/toph/CloudCheckin/checkin_runner.py:1).
- Base: `scheduler.py` calls `validate_target_cookies(parse_targets())` once at
  startup, before computing the first next-run timestamp.
- Bad: `scheduler.py` waits until the first cron execution to discover that the
  enabled target has neither a direct cookie nor a Cookie Cloud match.

### 6. Tests Required

- Syntax-check the runner, shared resolver, and affected platform modules with `python3 -m py_compile`.
- Syntax-check the scheduler entrypoint with `python3 -m py_compile scheduler.py`.
- Validate runner argument handling with an invalid `CHECKIN_TARGETS` value and assert non-zero exit plus a supported-target message.
- Validate startup cookie checks with direct-cookie success, Cookie Cloud
  success, missing-cookie failure, no raw secret output, and scheduler fail-fast
  behavior before the wait loop.
- Validate runner target logs by stubbing subprocess execution and asserting
  per-target start, success, failure, and first-failure stop behavior.
- Validate failed runner subprocesses still forward stdout/stderr and include a
  recent failure-output summary.
- Validate subprocess start failures are wrapped with the failing target/module
  context and stop later targets.
- Validate shared attendance behavior with isolated tests for multi-account cookies, request timeout propagation, and business failure responses.
- Validate platform module imports do not trigger check-in side effects.
- Validate deployment compose wiring with `docker compose config` after providing a local `.env` file copied from `.env.localtest.example`.
- Validate local build override wiring with `docker compose -f docker-compose.yml -f docker-compose.build.yml config`.
- Validate GitHub Actions workflow syntax with `actionlint`.
- When real credentials are available, run the affected module with `python -m ...`, `python run.py`, or the long-running container and assert the correct cookie source is used.

### 7. Wrong vs Correct

#### Wrong

Replace direct per-platform cookie support with a Cookie Cloud-only flow, or make the batch runner import platform modules directly:

```python
import nodeseek.nodeseek
cookie = fetch_cookiecloud_only("nodeseek.com")
```

#### Correct

Keep the original env contract, use Cookie Cloud only as fallback, and run existing module entrypoints through subprocesses:

```python
cookie = get_cookie_value("NODESEEK_COOKIE", ["nodeseek.com", "www.nodeseek.com"])
subprocess.run([sys.executable, "-m", "nodeseek.nodeseek"], check=False)
```

Do not turn "already completed today" into a hard failure:

```python
if signed:
    raise ValueError("Fail to check in")
```

Instead, treat it as an idempotent success path:

```python
if signed:
    print("V2EX already checked in today", flush=True)
    send_tg_notification(message)
```

Do not put cron parsing or sleep loops into `run.py`:

```python
while True:
    run_targets(parse_targets())
    time.sleep(86400)
```

Instead, keep one-shot execution and scheduling separate:

```python
next_run = croniter(cron_expression, now).get_next(datetime)
sleep_until(next_run)
run_targets(targets)
```

Do not let the long-running scheduler defer missing-cookie errors until the first
cron execution:

```python
targets = parse_targets()
while True:
    sleep_until(next_run)
    run_targets(targets)
```

Instead, validate safe cookie availability once before entering the wait loop:

```python
targets = parse_targets()
validate_target_cookies(targets)
while True:
    sleep_until(next_run)
    run_targets(targets)
```

---

## Testing Requirements

The repository now has a minimal `pytest` entrypoint configured through:

- [pyproject.toml](/home/toph/CloudCheckin/pyproject.toml:1)
- [pytest.ini](/home/toph/CloudCheckin/pytest.ini:1)
- [tests/test_checkin_response.py](/home/toph/CloudCheckin/tests/test_checkin_response.py:1)
- [tests/test_checkin_runner.py](/home/toph/CloudCheckin/tests/test_checkin_runner.py:1)

Minimum verification for backend changes:

- Run `python3 -m compileall` on affected modules when touching script entrypoints.
- Run `pytest` for shared helpers and parsing utilities that have isolated tests.
- Confirm required environment variables are documented or preserved.
- For parsing changes, verify against a real response sample or the live platform when safe.
- For scheduler or deployment changes, verify with `docker compose config` and a targeted local container run when possible.

When you add shared utilities or cross-platform response handling, prefer to extend
the `tests/` suite instead of leaving the behavior manual-only.

---

## Code Review Checklist

- Does the change match the existing package-per-platform structure?
- Are secrets still sourced only from environment variables?
- Are failure paths visible through stdout or container logs and, when appropriate, Telegram?
- Did the author reuse existing notification or captcha integration code where applicable?
- If a constant or endpoint changed, were all platform-specific copies searched first?
- Does the README or operational documentation need updating because local setup or secrets changed?

---

## Common Mistakes

- Adding a feature for one platform by copying another script and forgetting to rename environment variables or notification text.
- Logging too little to debug CI failures, or too much sensitive data.
- Changing an external request header or regex in one place without checking related platform variants or shared scheduler assumptions.
- Treating this project like a generic backend service and adding abstractions that make simple automation harder to trace.
- Making Docker support bypass the documented `python -m ...` flows, which creates different behavior between local runs and container runs.
