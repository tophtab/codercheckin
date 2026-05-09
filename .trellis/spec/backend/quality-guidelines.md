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
- Deployment compose file: `docker-compose.yml`
- Local build override file: `docker-compose.build.yml`
- Git ignore file: `.gitignore`
- Docker build context ignore file: `.dockerignore`

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
- Cookie Cloud domain matching must not treat arbitrary subdomains as matches
  for a requested registrable domain. A host matches when it is exactly one of
  the requested domains, or when the requested domain is a child of the Cookie
  Cloud cookie host.
- When Cookie Cloud returns duplicate cookie names from multiple matching hosts,
  the most specific matching host wins. For example, `www.v2ex.com` must
  override `v2ex.com` for the same cookie name when both hosts are requested.
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
  start and success/failure result, continue after failed targets, and raise
  after all configured targets have been attempted when any target failed.
- `run_targets()` must also wrap subprocess start failures with the failing
  target/module context and a bounded recent output summary, then continue with
  later configured targets.
- The final `run_targets()` exception must preserve useful failed-target
  context. When multiple targets fail, it must make the aggregate failure clear
  and summarize each failed target instead of hiding all but the first failure.
- `run_targets()` must forward target subprocess stdout/stderr while the target
  runs and, on failure, print a bounded recent stdout/stderr summary without
  introducing new secret sources beyond the subprocess output itself.
- Docker Compose on the NAS or local host is the supported runtime deployment
  contract.
- GitHub Actions is the supported Docker image publishing contract: build the
  repository image from `Dockerfile`, push it to Docker Hub, then update the NAS
  with `docker compose pull` and `docker compose up -d`.
- CircleCI and Cloudflare Workers are out of scope for this repository and
  should not be reintroduced as tracked deployment files.
- Because the Dockerfile uses `COPY . .`, `.dockerignore` must exclude local
  secrets, agent/editor tooling, Trellis metadata, test-only files, caches,
  virtualenvs, packaging artifacts, local compose files, and build helper
  directories that are not needed by the runtime scheduler image.
- Docker image slimming must preserve the `python:3.11-slim` base image and
  runtime dependencies unless there is an explicit compatibility test plan.
  Low-risk dependency install slimming may remove pip self-upgrades, install
  with `pip install --no-cache-dir --no-compile -r requirements.txt`, and clean
  generated `*.pyc` / `__pycache__` files from `/usr/local/lib/python3.11` in
  the same image layer.
- `.gitignore` must keep local secrets, Python caches, pytest/mypy/ruff caches,
  virtualenvs, coverage output, package metadata, and build outputs out of git
  history, while keeping checked-in examples such as `.env.localtest.example`.
- `tests/` is repository quality infrastructure: keep it tracked and exclude it
  from runtime Docker images instead of deleting it from the repository.

### 4. Validation & Error Matrix

| Condition | Expected Behavior |
|----------|-------------------|
| Direct platform cookie is set | Use it immediately and skip Cookie Cloud |
| Direct platform cookie missing, Cookie Cloud configured, matching domain found | Use Cookie Cloud cookie and print a safe success hint |
| Cookie Cloud returns duplicate names for `v2ex.com` and `www.v2ex.com` | Build one cookie header where the `www.v2ex.com` value wins for duplicated names |
| Cookie Cloud returns cookies only for an unrelated subdomain such as `api.v2ex.com` | Do not use those cookies for a `v2ex.com` / `www.v2ex.com` lookup |
| Direct platform cookie missing, Cookie Cloud not configured | Return empty string and let the platform entrypoint raise `ValueError` |
| Cookie Cloud request fails or returns bad JSON | Print a safe error, return empty string, and let the platform entrypoint fail fast |
| Scheduler startup target has direct cookie or Cookie Cloud match | Log the safe cookie source and continue to scheduling |
| Scheduler startup target has no direct cookie and no Cookie Cloud match | Exit non-zero before logging the next scheduled run |
| `CHECKIN_TARGETS` contains unsupported names | `run.py` exits non-zero with the supported target list |
| A check-in target subprocess exits non-zero | `run_targets()` logs the target failure, continues to later targets, then raises after all targets have been attempted |
| A check-in target subprocess cannot start | `run_targets()` logs a target-specific failure that preserves the module/startup error text, continues to later targets, then raises after all targets have been attempted |
| Platform reports "already checked in" | Treat as a successful, idempotent run instead of failing the batch |
| Platform JSON returns `success: false` | Treat as a business failure even if HTTP status is `200`, unless the message is an idempotent already-checked-in response |
| Platform module is imported by tests or tooling | Import succeeds without cookie lookup, sleeps, HTTP requests, or Telegram sends |
| `CHECKIN_CRON` is invalid | `scheduler.py` exits non-zero before entering the loop |
| `TZ` is invalid | `scheduler.py` exits non-zero before entering the loop |
| Server runs `docker compose` with default files | Compose pulls `CLOUDCHECKIN_IMAGE` instead of building locally |
| Local developer needs to build current source | Compose uses `docker-compose.build.yml` as an explicit override |
| Docker image is built from the repository root | `/app` contains runtime Python modules and `requirements.txt`, but not `.env`, `.agents`, `.codex`, `.claude`, `.cursor`, `.trellis`, `.venv`, `.pytest_cache`, or `tests` |
| Low-risk Docker image slimming is applied | Image still builds from `python:3.11-slim`, scheduler starts with placeholder cookie config, and `/usr/local/lib/python3.11` contains no generated `*.pyc` or `__pycache__` files |
| Local generated/cache directories exist after development or tests | They are ignored by git and may be deleted locally; source tests remain tracked |
| Docker image publication is needed | Use the GitHub Actions Docker Hub publish workflow with Docker Hub secrets and no checked-in credentials |
| CircleCI or Worker deployment files are proposed | Reject them as out of scope for the Docker/NAS deployment contract |

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
- Validate Cookie Cloud duplicate cookie names across parent and host-specific
  domains, and validate that unrelated subdomain cookies are ignored.
- Validate runner target logs by stubbing subprocess execution and asserting
  per-target start, success, failure, and continue-after-failure behavior.
- Validate failed runner subprocesses still forward stdout/stderr and include a
  recent failure-output summary.
- Validate subprocess start failures are wrapped with the failing target/module
  context and do not stop later targets.
- Validate multiple target failures raise an aggregate message that summarizes
  every failed target.
- Validate shared attendance behavior with isolated tests for multi-account cookies, request timeout propagation, and business failure responses.
- Validate platform module imports do not trigger check-in side effects.
- Validate deployment compose wiring with `docker compose config` after providing a local `.env` file copied from `.env.localtest.example`.
- Validate local build override wiring with `docker compose -f docker-compose.yml -f docker-compose.build.yml config`.
- Validate Docker build context hygiene with a local image build and an image
  contents check that confirms runtime files are present and ignored
  development, cache, test, metadata, and secret paths are absent from `/app`.
- Validate low-risk Docker image slimming with a local image build, a scheduler
  smoke run using placeholder direct-cookie configuration, and an image contents
  check for absent `/usr/local/lib/python3.11` `*.pyc` / `__pycache__` files.
- Validate repository cleanup with `git status --ignored` or targeted `git
  ls-files` checks when changing ignore rules, and do not remove tracked tests
  as a substitute for excluding them from the runtime image.
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
    log("V2EX already checked in today")
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

Do not stop the target loop at the first failed subprocess:

```python
for target in targets:
    returncode = run_target(target)
    if returncode != 0:
        raise TargetExecutionError(target=target, returncode=returncode)
```

Instead, collect target failures, continue with later configured targets, and
raise only after the full target list has been attempted:

```python
failures = []
for target in targets:
    returncode = run_target(target)
    if returncode != 0:
        failures.append(TargetExecutionError(target=target, returncode=returncode))
        continue

if failures:
    raise failures[0] if len(failures) == 1 else MultipleTargetExecutionError(failures)
```

---

## Scenario: V2EX Daily Mission Confirmation

### 1. Scope / Trigger

- Trigger: changing the V2EX daily mission request flow, success detection, or
  optional balance parsing in [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:1).

### 2. Signatures

- Daily mission page: `GET https://www.v2ex.com/mission/daily`
- Redeem URL shape: `GET https://www.v2ex.com/mission/daily/redeem?once=<token>`
- Mission action helper signature: `get_daily_mission_action(headers: dict[str, str], message: str, session: requests.Session | None = None) -> tuple[str | None, bool, str]`
- Check-in helper signature: `check_in(action_url: str, headers: dict[str, str], message: str, session: requests.Session | None = None) -> tuple[bool, str]`
- Balance helper signature: `balance(headers: dict[str, str], session: requests.Session | None = None) -> tuple[str | None, str | None]`

### 3. Contracts

- The daily mission action URL is parsed from the V2EX page action/button and
  normalized to `https://www.v2ex.com`.
- First-run V2EX mission, redeem, and balance confirmation requests must share
  one `curl_cffi.requests.Session()` seeded from the resolved `V2EX_COOKIE`
  value so cookies issued by earlier responses are sent to later requests.
- Session-backed V2EX requests should rely on the session cookie jar instead of
  passing a raw `cookie` request header.
- The action URL can contain a `once` token and must not be logged or copied
  into user-facing status messages.
- A mission action URL pointing to `/balance` means the daily mission is already
  complete and must be treated as an idempotent success.
- A redeem action URL must be requested with `curl_cffi` and a finite timeout.
- A page containing `每日登录奖励已领取` means the daily mission is complete.
- A login page marker means the cookie is expired or unauthenticated.
- After a redeem action, today's `/balance` `每日登录奖励` entry is the
  authoritative success proof; redeem response markers alone are not sufficient.
- Balance parsing is supplemental after a successful redeem; missing balance
  data must not convert the check-in into a failure.

### 4. Validation & Error Matrix

| Condition | Expected Behavior |
|----------|-------------------|
| Initial mission page already says reward claimed | Treat as successful idempotent run |
| Mission action points to `/balance` | Treat as successful idempotent run |
| Mission action points to redeem and today's balance page has a daily reward entry | Treat as successful check-in |
| Redeem response says success but today's balance page lacks a daily reward entry | Fail with a clear V2EX balance confirmation message |
| Redeem response indicates login required | Treat as failure |
| Mission page has no supported action | Fail without logging raw action or token data |
| Balance parsing fails after successful redeem | Log the parsing failure, send the normal notification, and return success |

### 5. Good / Base / Bad Cases

- Good: the mission page button points to `/mission/daily/redeem?once=...`,
  redeem returns a changed or redirected page, `/balance` contains today's
  `每日登录奖励`, and the job returns success.
- Base: the mission page button points to `/balance`, so the job returns an
  idempotent already-signed success without requesting a redeem URL.
- Bad: redeem returns `已成功领取每日登录奖励`, but `/balance` does not contain
  today's daily reward entry; do not treat the redeem response body alone as
  success.

### 6. Tests Required

- Test that the mission action parser extracts a V2EX-style button `onclick`
  action and normalizes relative URLs.
- Test that an action pointing to `/balance` is treated as an idempotent
  already-signed success.
- Test that `check_in()` requests the parsed redeem action and succeeds when
  `/balance` contains today's daily reward entry.
- Test that cookies issued during the mission page request are available to the
  redeem request and the balance confirmation request through one shared
  session.
- Test that `check_in()` fails when redeem runs but `/balance` does not confirm
  today's daily reward, even if the redeem response contains a success marker.
- Test that `check_in()` fails when the redeem response indicates login is
  required.
- Test that `main()` keeps a successful return code and sends the success
  notification when balance parsing returns `(None, None)`.
- Assert logs never include action URLs, `once` tokens, or cookie values.

### 7. Wrong vs Correct

#### Wrong

```python
success, message = check_in(action_url, headers, message)
if success and balance(headers) == (None, None):
    raise ValueError("V2EX balance parsing failed")
```

#### Correct

```python
success, message = check_in(action_url, headers, message)
if success and balance(headers) == (None, None):
    log("V2EX balance parsing failed after successful redeem")
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
