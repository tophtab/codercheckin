# Research: timerring CloudCheckin upstream comparison

- Query: Research `https://github.com/timerring/CloudCheckin` for Docker-oriented V2EX check-in behavior, repository structure, CI/CD/Cloudflare Workers presence, and adaptation guidance for this repository's V2EX confirmation task.
- Scope: mixed
- Date: 2026-05-08

## Findings

### Files Found

- `v2ex/v2ex.py` - this repository's V2EX module, now structured around import-safe helpers, `curl_cffi`, finite timeouts, Cookie Cloud fallback, balance confirmation, runtime logging, and Telegram notification.
- `tests/test_v2ex.py` - focused local V2EX tests for mission action parsing, `/balance` idempotency, post-redeem balance confirmation, login failure, and no token leakage.
- `.trellis/tasks/05-08-fix-v2ex-redeem-confirmation/prd.md` - task contract requiring action parsing from the V2EX daily page and today's `/balance` daily reward as authoritative success proof.
- `.trellis/spec/backend/quality-guidelines.md` - local backend contracts for secrets, `curl_cffi`, finite timeouts, Cookie Cloud fallback, Docker/NAS runner behavior, and V2EX daily mission confirmation.
- External: `https://github.com/timerring/CloudCheckin` - upstream project page.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/v2ex/v2ex.py` - upstream Python V2EX implementation inspected from `main`.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/cloudflareworkers/src/v2ex.js` - upstream Cloudflare Worker V2EX experiment inspected from `main`.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/README.md` - upstream README inspected from `main`.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/.circleci/config.yml` - upstream CircleCI pipeline inspected from `main`.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/.github/workflows/deploy-circleci.yml` - upstream GitHub workflow for CircleCI context sync inspected from `main`.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/.github/workflows/setup-workers.yml` - upstream GitHub workflow for Cloudflare Worker deployment inspected from `main`.
- External: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/worker.js` and `https://raw.githubusercontent.com/timerring/CloudCheckin/main/wrangler.toml` - upstream root Cloudflare Worker scheduler inspected from `main`.

### External Repository Structure

- Upstream root contains `.circleci/`, `.github/`, `cloudflareworkers/`, platform modules `nodeseek/`, `deepflood/`, `v2ex/`, `onepoint3acres/`, shared `telegram/`, `requirements.txt`, `worker.js`, and `wrangler.toml`.
- Upstream `.github/workflows/` contains two workflows: `deploy-circleci.yml` and `setup-workers.yml`; no Docker Hub publishing workflow was found in upstream.
- Upstream `cloudflareworkers/` contains `README.md`, `src/nodeseek.js`, `src/v2ex.js`, `wranglernode.toml`, and `wranglerv2ex.toml`.
- Upstream root `worker.js` is a Cloudflare Worker scheduled handler that posts `env.CIRCLECI_WEBHOOK_URL`; root `wrangler.toml` defines `name = "circleci-scheduler"`, `main = "worker.js"`, and a daily UTC cron.
- Upstream README describes the project as based on CI/CD plus Cloudflare Workers; the architecture is Cloudflare Worker scheduler -> CircleCI webhook -> platform requests -> Telegram/email notification.
- Upstream README explicitly says Cloudflare Worker direct platform requests were tried, but deployed Worker traffic can be limited by platform anti-abuse signals; the current main workflow uses Workers as a scheduler/webhook trigger rather than the primary platform check-in runtime.

### External V2EX Behavior

- Upstream Python `v2ex/v2ex.py` imports `curl_cffi.requests` and builds browser-like headers with `V2EX_COOKIE` from the environment at module import time.
- Upstream Python `get_once()` loads `/mission/daily`, checks the Chinese login marker `需要先登录`, checks already-claimed marker `每日登录奖励已领取`, extracts a raw `once` token using `redeem\?once=(.*?)'`, and appends the raw token to its status message.
- Upstream Python `check_in(once)` constructs `/mission/daily/redeem?once=<once>`, requests it, and treats redeem response text containing `已成功领取每日登录奖励` as success.
- Upstream Python `balance()` fetches `/balance` and parses a `每日登录奖励` row, but the main flow only calls balance after a successful redeem response. It does not use today's `/balance` entry as the primary post-redeem success proof.
- Upstream Python main treats the already-signed path as failure because when `once` is absent it appends `FAIL.`, sends Telegram, and raises. This conflicts with this repo's idempotent success contract.
- Upstream Python requests do not pass an explicit timeout to `requests.get(...)`.
- Upstream Cloudflare Worker `cloudflareworkers/src/v2ex.js` also extracts `once` with a regex and logs the token in normal logs. Its `checkIn()` function checks the redeem response body for `已成功领取每日登录奖励`, but the call is commented out in `handleCheckin()`, so the Worker V2EX variant appears experimental rather than the production path to copy.
- Upstream CircleCI config installs `curl_cffi python-dotenv` for the V2EX job and runs `python -m v2ex.v2ex`.

### Current Repository Code Patterns

- `v2ex/v2ex.py:8` keeps V2EX HTTP on `curl_cffi.requests`.
- `v2ex/v2ex.py:11-14` reuses project config, Cookie Cloud resolver, timestamped runtime log, and shared Telegram notification.
- `v2ex/v2ex.py:24-30` centralizes mission action parsing and V2EX endpoint constants.
- `v2ex/v2ex.py:50-59` normalizes parsed actions to `https://www.v2ex.com` and only accepts `/balance` or `/mission/daily/redeem`.
- `v2ex/v2ex.py:70-99` parses `onclick` location assignment through `HTMLParser` and does not log the parsed action URL.
- `v2ex/v2ex.py:102-125` builds browser-like headers and uses `_fetch_page()` with `REQUEST_TIMEOUT_SECONDS`.
- `v2ex/v2ex.py:150-189` parses `/balance` daily reward rows and confirms that a `每日登录奖励` entry belongs to today's local date.
- `v2ex/v2ex.py:192-212` treats login pages as failure, mission already-claimed marker as success, `/balance` actions as idempotent success, and redeem actions as the next step.
- `v2ex/v2ex.py:215-243` executes a redeem action, keeps login-page failure, and requires today's `/balance` daily reward for success instead of trusting the redeem response body.
- `v2ex/v2ex.py:256-287` keeps `load_dotenv()`, `get_cookie_value("V2EX_COOKIE", ["v2ex.com", "www.v2ex.com"])`, shared Telegram notification, and supplemental non-fatal balance parsing after success.
- `tests/test_v2ex.py:56-87` verifies V2EX-style `onclick` action parsing and token-safe status/log output.
- `tests/test_v2ex.py:90-103` verifies a `/balance` action is treated as already signed.
- `tests/test_v2ex.py:106-145` verifies redeem is requested first and today's `/balance` entry confirms success without logging the once token.
- `tests/test_v2ex.py:155-191` verifies a redeem success marker alone is not enough when `/balance` does not confirm today's reward.
- `tests/test_v2ex.py:194-233` verifies login-page and redeem-exception failures stay token-safe.
- `tests/test_v2ex.py:236-301` verifies balance row parsing keeps timestamps tied to their own rows and ambiguous balance data fails confirmation.
- `tests/test_v2ex.py:304-340` verifies supplemental balance parsing failure after successful check-in is logged but not fatal.

### Adaptation Guidance

- Do not copy upstream's CI/CD runtime shape into this repository. This repo's task and spec require preserving Docker/NAS deployment contracts; upstream is CircleCI plus Cloudflare Worker scheduler oriented.
- Do not copy upstream's module-import cookie lookup. This repository requires import-safe modules; cookie lookup belongs in `main()` or injected helpers.
- Do not copy upstream's raw `once` logging or status message. This repository explicitly forbids logging token-bearing action URLs, `once` values, cookies, and full authenticated headers.
- Do not copy upstream's "already signed" failure behavior. This repository treats already-complete platform state as a successful idempotent run.
- Do not copy upstream's response-body-only success check. The PRD requires redeem action execution followed by today's `/balance` `每日登录奖励` entry as authoritative confirmation.
- Keep useful upstream pieces only where they agree with local contracts: `curl_cffi`, browser-like headers, `/mission/daily`, `/mission/daily/redeem?once=...`, `/balance`, login-page detection, and the Chinese daily reward markers.
- Cloudflare Worker artifacts in upstream are useful as evidence of approaches not to introduce here: Worker direct V2EX check-in logs token-bearing URLs and upstream README warns deployed Worker traffic can trigger platform limitations.

### Related Specs

- `.trellis/tasks/05-08-fix-v2ex-redeem-confirmation/prd.md:5-10` requires action parsing and `/balance` confirmation while preserving `curl_cffi`, Cookie Cloud, timestamped logging, Telegram, and no secret leakage.
- `.trellis/tasks/05-08-fix-v2ex-redeem-confirmation/prd.md:30-43` requires parsing the V2EX action, treating `/balance` as idempotent success, confirming today's balance reward, preserving login failure, and not changing Docker/proxy/scheduler/Telegram/Cookie Cloud.
- `.trellis/tasks/05-08-fix-v2ex-redeem-confirmation/prd.md:67-79` scopes implementation to `v2ex/v2ex.py`, standard-library or narrowly scoped parsing, `curl_cffi`, and supplemental non-fatal `balance(headers)` after success.
- `.trellis/spec/backend/quality-guidelines.md:24-28` forbids hardcoded secrets, switching anti-bot flows back to plain `requests`, duplicating Telegram notification logic, ignoring missing parsed data, and unnecessary abstractions.
- `.trellis/spec/backend/quality-guidelines.md:34-39` requires `load_dotenv()`, config validation before network calls, platform constants near use, import-safe modules, non-zero failure exits, and reuse of existing helpers.
- `.trellis/spec/backend/quality-guidelines.md:75-98` preserves direct env cookie priority, Cookie Cloud fallback, safe startup validation, import safety, and finite external request timeouts.
- `.trellis/spec/backend/quality-guidelines.md:142-144` says already-completed platform state is success and platform imports must have no side effects.

### External References

- Upstream repository: `https://github.com/timerring/CloudCheckin`
- Upstream Python V2EX raw source: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/v2ex/v2ex.py`
- Upstream Worker V2EX raw source: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/cloudflareworkers/src/v2ex.js`
- Upstream README raw source: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/README.md`
- Upstream CircleCI config raw source: `https://raw.githubusercontent.com/timerring/CloudCheckin/main/.circleci/config.yml`
- Upstream GitHub workflow directory API: `https://api.github.com/repos/timerring/CloudCheckin/contents/.github/workflows?ref=main`
- Upstream Cloudflare Workers directory API: `https://api.github.com/repos/timerring/CloudCheckin/contents/cloudflareworkers?ref=main`

## Caveats / Not Found

- No Dockerfile, docker-compose file, Docker Hub publishing workflow, Cookie Cloud integration, or Docker/NAS scheduler contract was found in upstream `timerring/CloudCheckin` on `main`. Docker-oriented behavior appears to be local to this repository/fork, not an upstream pattern to mirror.
- Upstream line numbers were inspected from live `main` raw files on 2026-05-08 and may shift if upstream changes.
- The upstream Cloudflare Worker V2EX implementation appears experimental and includes token-leaking logs; it should not be treated as a safe implementation reference.
- The GitHub API output used for repository structure is unauthenticated and subject to rate limits.
