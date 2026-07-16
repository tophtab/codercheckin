# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

The project is a Python 3.11 package tested with pytest. Current quality
expectations are pragmatic: keep modules small, preserve CLI behavior, inject
side effects in tests, and protect secrets from logs.

Run the pytest suite before considering backend changes complete.

---

## Forbidden Patterns

- Do not perform cookie lookup or network work at platform module import time.
  `tests/test_platform_imports.py` verifies platform imports do not trigger
  cookie resolution.
- Do not duplicate target definitions outside `checkin_runner.TARGETS`.
  Platform registration, cookie environment names, and domains belong there.
- Do not log direct cookies, Cookie Cloud cookie values, Telegram credentials, or
  V2EX action tokens.
- Do not add unbounded network calls. Use `REQUEST_TIMEOUT_SECONDS`.
- Do not sleep in tests. Functions with delays should keep injectable callables,
  as `run_attendance_checkin` does with `sleep` and `randint`.
- Do not silently swallow target failures in orchestration. Preserve recent
  output and raise a contextual target exception after all targets run.

---

## Required Patterns

- Prefer dependency injection for side effects that tests need to control:
  cookie resolution, notification delivery, sleeping, random delay generation,
  HTTP posting, subprocess creation, and time providers.
- Keep browser identity constants centralized in `config.py` and reuse them in
  platform modules.
- Load `.env` inside runtime entrypoints or platform `main()` functions, not
  during tests through hidden global setup. `telegram/notify.py` currently calls
  `load_dotenv()` at import; avoid spreading that pattern.
- For similar attendance APIs, use `AttendanceConfig` plus
  `run_attendance_checkin` instead of copying a full check-in loop.
- For success parsing, route attendance-style responses through
  `is_successful_checkin_response` so explicit false business responses remain
  failures and already-signed messages are treated as success.
- For multi-account cookies, preserve the existing `&` separator behavior and
  trim empty entries.
- Keep entrypoints returning integer exit codes from `main()` where practical,
  then call `sys.exit(main())` under the `__main__` guard.

## Runtime Contracts

These contracts are important enough to check explicitly during review:

- Direct cookie environment variables have first priority:
  `NODESEEK_COOKIE`, `DEEPFLOOD_COOKIE`, and `V2EX_COOKIE`.
- Cookie Cloud is optional and only used when the direct platform variable is
  empty.
- Cookie Cloud configuration uses environment variables only:
  `COOKIE_CLOUD_URL`, `COOKIE_CLOUD_UUID`, `COOKIE_CLOUD_PASSWORD`, and
  `COOKIE_CLOUD_CRYPTO_TYPE`.
- Cookie Cloud domain matching must not treat arbitrary subdomains as matches
  for a requested domain. A host matches when it is exactly one of the requested
  domains, or when the requested domain is a child of the Cookie Cloud cookie
  host.
- Duplicate Cookie Cloud cookie names are resolved by host specificity:
  `www.v2ex.com` overrides `v2ex.com` for the same cookie name when both are
  requested.
- The scheduler validates cookie availability for every configured target before
  entering the wait loop.
- External requests must set a finite timeout so NAS scheduler subprocesses do
  not hang indefinitely on one platform.
- `run_targets` executes configured targets in order, logs each target start and
  success/failure result, continues after failures, and raises after all targets
  have been attempted.
- Target subprocess stdout/stderr is forwarded while the process runs. On
  failure, include a bounded recent stdout/stderr summary.
- Docker Compose is the supported NAS deployment contract. GitHub Actions is the
  supported Docker image publishing contract. Do not reintroduce CircleCI or
  Cloudflare Worker deployment files.
- Keep `curl_cffi` pinned to `0.14.0` in both `requirements.txt` and
  `pyproject.toml`. Version `0.15.0` reproduces curl error 35 with
  `OPENSSL_internal:invalid library` when connecting to V2EX from the project's
  `python:3.11-slim` image; validate upgrades inside that image against the
  V2EX daily mission URL before changing the pin.
- Docker Hub publishing resolves the target image from `vars.DOCKERHUB_IMAGE`
  when set; otherwise it falls back to
  `$DOCKERHUB_USERNAME/codercheckin`. Keep Compose defaults, README examples,
  and the workflow fallback aligned to the `codercheckin` image name.

## V2EX Daily Mission Contract

- Parse the daily mission action URL from the V2EX page and normalize it to
  `https://www.v2ex.com`.
- First-run mission, redeem, and balance confirmation requests must share one
  `curl_cffi.requests.Session` seeded from `V2EX_COOKIE` so cookies issued by
  earlier responses reach later requests.
- Session-backed V2EX requests should rely on the session cookie jar instead of
  passing a raw `cookie` request header.
- The action URL can contain a `once` token and must not be logged or copied
  into user-facing status messages.
- A mission action pointing to `/balance` means the daily mission is already
  complete and must be treated as success.
- After a redeem action, today's `/balance` `每日登录奖励` entry is the
  authoritative success proof. Redeem response markers alone are not sufficient.
- Balance parsing is supplemental after a successful redeem. Missing balance
  amount data should log a parsing failure but must not convert a confirmed
  check-in into a failure.

---

## Testing Requirements

- Add or update pytest coverage for every behavior change.
- Use `monkeypatch` to replace environment variables, network calls,
  subprocesses, time providers, and module functions.
- Use `capsys` plus `tests.log_assertions.assert_timestamped_lines` when testing
  logged output.
- Assert negative security properties when relevant: no cookie values, no V2EX
  `once` tokens, and no credentials in logs or user-facing status messages.
- Test both direct environment cookie and Cookie Cloud fallback paths when
  changing cookie resolution.
- For scheduler changes, test timezone-aware timestamps, cron validation,
  startup validation ordering, and failure propagation.
- For target runner changes, test success, single failure, multiple failures,
  subprocess start failure, stdout/stderr forwarding, and recent output limits.
- Validate V2EX balance parsing against real reward row shapes, including a
  description cell like `每日登录奖励 9 铜币`, and assert the success message/log
  includes the parsed copper amount.
- Validate deployment compose wiring with `docker compose config` when changing
  Docker files.
- Validate Docker image build context hygiene when changing `.dockerignore` or
  the Dockerfile: runtime files should be present, while local secrets,
  metadata, caches, virtualenvs, and tests should be excluded from the image.

---

## Code Review Checklist

- Does the change keep platform-specific behavior in the platform package and
  shared orchestration in root helpers?
- Are all new network calls bounded by `REQUEST_TIMEOUT_SECONDS`?
- Are secrets excluded from logs, exception messages, notifications, and tests?
- If a target fails, does the runner still attempt remaining targets and report
  contextual recent output?
- Are already-signed states treated as successful check-ins where the target
  semantics require that?
- Do tests avoid real network, real sleeps, real subprocess work, and dependence
  on the machine's current time?
- Does `pytest` pass from the repository root?

## Wrong vs Correct

Do not replace direct per-platform cookie support with a Cookie Cloud-only flow:

```python
# Wrong
cookie = fetch_cookiecloud_only("nodeseek.com")
```

Keep the original environment contract and use Cookie Cloud only as fallback:

```python
# Correct
cookie = get_cookie_value("NODESEEK_COOKIE", ["nodeseek.com", "www.nodeseek.com"])
```

Do not turn an already-completed check-in into a hard failure:

```python
# Wrong
if signed:
    raise ValueError("Fail to check in")
```

Treat it as an idempotent success:

```python
# Correct
if signed:
    log("V2EX already checked in today")
    send_tg_notification(message)
```

Do not put cron parsing or sleep loops into `run.py`. Keep scheduling in
`scheduler.py` and one-shot execution in `run.py`.
