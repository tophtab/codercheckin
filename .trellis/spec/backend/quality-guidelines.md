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
- Exit with a non-zero code when a scheduled task fails.
- Reuse existing helpers and data modules before adding new utility code.

Examples:

- Shared Telegram helper reuse in [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:6), [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:7), and [deepflood/deepflood.py](/home/toph/CloudCheckin/deepflood/deepflood.py:7).
- Environment validation in [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:102).
- Local debug execution commands in [README.md](/home/toph/CloudCheckin/README.md:153).

## Scenario: Docker scheduler, runner, and Cookie Cloud fallback

### 1. Scope / Trigger

- Trigger: changing Docker deployment files, batch or scheduler entrypoints, or the way platform cookies are resolved from environment variables.

### 2. Signatures

- One-shot batch entrypoint command: `python run.py`
- Long-running scheduler entrypoint command: `python scheduler.py`
- Batch target selector env: `CHECKIN_TARGETS=nodeseek,deepflood,v2ex`
- Scheduler timezone env: `TZ=Asia/Shanghai`
- Scheduler cron env: `CHECKIN_CRON=0 3 * * *`
- Deployment image env: `CLOUDCHECKIN_IMAGE=tophtab/cloudcheckin:latest`
- Shared resolver signature: `get_cookie_value(env_name: str, domains: list[str]) -> str`
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
- If no direct cookie exists and Cookie Cloud cannot provide a matching domain cookie, the platform script must still fail fast before making network requests.
- `CHECKIN_CRON` must be a valid 5-field cron expression.
- `TZ` must be a valid IANA timezone name accepted by `zoneinfo`.
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
| `CHECKIN_TARGETS` contains unsupported names | `run.py` exits non-zero with the supported target list |
| Platform reports "already checked in" | Treat as a successful, idempotent run instead of failing the batch |
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
- Good: [scheduler.py](/home/toph/CloudCheckin/scheduler.py:1) starts with `TZ=Asia/Shanghai` and `CHECKIN_CRON=0 3 * * *`, logs the next run, and then delegates to [checkin_runner.py](/home/toph/CloudCheckin/checkin_runner.py:1).

### 6. Tests Required

- Syntax-check the runner, shared resolver, and affected platform modules with `python3 -m py_compile`.
- Syntax-check the scheduler entrypoint with `python3 -m py_compile scheduler.py`.
- Validate runner argument handling with an invalid `CHECKIN_TARGETS` value and assert non-zero exit plus a supported-target message.
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

---

## Testing Requirements

There is no automated test suite in the repository today.
That is current reality and the documentation should reflect it honestly.

Minimum verification for backend changes:

- Run the affected module locally with `python -m ...` when possible.
- Confirm required environment variables are documented or preserved.
- For parsing changes, verify against a real response sample or the live platform when safe.
- For scheduler or deployment changes, verify with `docker compose config` and a targeted local container run when possible.

If you add a non-trivial parsing helper, retry policy, or shared utility, prefer to
add isolated tests rather than expanding the current manual-only model further.

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
