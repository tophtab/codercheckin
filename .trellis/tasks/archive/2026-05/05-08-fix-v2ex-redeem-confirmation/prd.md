# Rework V2EX Docker Flow And Remove CI/Workers

## Goal

Refactor the V2EX check-in implementation for this Docker/NAS project using
`timerring/CloudCheckin` as the upstream behavioral reference where it fits,
while preserving this repo's runtime contracts: Docker Compose scheduling,
`curl_cffi` HTTP, Cookie Cloud fallback, timestamped logging, Telegram
notification, finite request timeouts, import-safe modules, and no secret
leakage. Remove CI/CD and Cloudflare Workers artifacts because this project no
longer considers those deployment modes.

## What I Already Know

* The deployment image was current; Docker Hub `latest` matched the expected
  digest.
* The deployment host must use a proxy, and manual Docker execution through that
  environment can reach V2EX.
* Cookie Cloud resolves a valid V2EX cookie for member `TophTab`.
* The V2EX balance page showed the 2026-05-08 daily reward only after the later
  manual run, so the 08:17 scheduled Docker run should be treated as a real
  failure.
* `timerring/CloudCheckin` uses `curl_cffi` for the Python V2EX job and the
  same V2EX endpoints/Chinese markers, but its upstream deployment model is
  CircleCI plus Cloudflare Workers rather than Docker.
* Upstream V2EX code has behaviors this repo should not copy directly:
  module-import cookie lookup, no explicit timeout, raw `once` token in status
  text, and already-signed treated as failure.
* This repo must not switch V2EX back to plain `requests`; it uses
  `curl_cffi.requests` for anti-bot compatibility.
* This repo has a tracked GitHub Actions Docker publishing workflow plus empty
  local `.circleci/` and `cloudflareworkers/` directories.

## Requirements

* Keep V2EX Python execution Docker-friendly via `python -m v2ex.v2ex`; do not
  add CI/CD or Worker-specific runtime assumptions.
* Use timerring's useful V2EX pieces: `curl_cffi`, `/mission/daily`,
  `/mission/daily/redeem?once=...`, `/balance`, login marker
  `需要先登录`, already-claimed marker `每日登录奖励已领取`, and redeem success marker
  `已成功领取每日登录奖励`.
* Preserve this repo's safer differences: cookie lookup in `main()`, Cookie
  Cloud fallback, finite timeouts, idempotent already-signed success, no token
  leakage, and balance confirmation after redeem.
* Execute V2EX redeem with `curl_cffi` and confirm successful completion using
  today's `/balance` `每日登录奖励` entry.
* Preserve login-page detection as a failure.
* Do not log action URLs containing tokens, `once` values, cookie values, full
  headers, or raw authenticated HTML.
* Remove CI/CD and Cloudflare Workers artifacts from the repository.
* Update `.trellis/spec/` so future work treats Docker/NAS as the supported
  deployment contract and does not reintroduce CI/CD or Worker files.
* Keep scheduler, proxy, Telegram, and Cookie Cloud contracts otherwise intact.

## Acceptance Criteria

* [ ] V2EX check-in keeps using `curl_cffi` and finite timeouts.
* [ ] V2EX check-in is import-safe and resolves cookies only at runtime via the
      existing direct-env/Cookie Cloud resolver.
* [ ] Already-signed V2EX state is treated as success.
* [ ] A redeem action/request is followed by today's `/balance` daily reward
      confirmation.
* [ ] If redeem executes but `/balance` does not contain today's daily reward,
      the check-in fails with a clear V2EX message.
* [ ] Login-page responses continue to fail.
* [ ] Tests assert token-bearing action URLs / `once` values are not logged.
* [ ] CI/CD and Cloudflare Workers tracked files are removed; empty local
      directories are cleaned up where present.
* [ ] Specs no longer describe GitHub Actions/CircleCI/Cloudflare Workers as
      supported deployment contracts.
* [ ] Targeted V2EX tests pass.

## Definition of Done

* Tests added or updated for the new confirmation behavior.
* Affected Python files compile.
* Project lint/type-check/test commands are run where available.
* Docker/NAS deployment remains supported.
* CI/CD and Cloudflare Worker docs/spec contracts are removed.
* Proxy, Telegram, and Cookie Cloud contracts are otherwise unchanged.

## Technical Approach

Rewrite or adjust the V2EX mission flow inside `v2ex/v2ex.py` while preserving
the module entrypoint and repo integrations:

* Fetch `/mission/daily` with `curl_cffi`.
* Derive the redeem action/token using a safe parser compatible with V2EX's
  current daily mission HTML and timerring's endpoint assumptions.
* Request the redeem action with `curl_cffi`.
* Use today's balance entry as the primary post-action success proof.
* Keep `balance(headers)` supplemental after successful check-in; do not make
  balance parsing failure fatal when success is already confirmed.
* Delete `.github/workflows/dockerhub-publish.yml` and remove empty
  `.circleci/` / `cloudflareworkers/` directories if present locally.
* Update `.trellis/spec/backend/quality-guidelines.md` and related specs so
  Docker Compose/NAS is the deployment contract and CI/CD/Workers are explicitly
  out of scope.

## Decision (ADR-lite)

**Context**: `timerring/CloudCheckin` is the upstream project, but upstream is
CI/CD/Cloudflare Worker oriented and contains V2EX behaviors that conflict with
this Docker/NAS fork's security and reliability contracts.

**Decision**: Use upstream only as a V2EX endpoint/marker/reference baseline.
Preserve this fork's Docker Compose runtime, Cookie Cloud, finite timeouts,
idempotent already-complete success, and secret-safe logging. Remove CI/CD and
Cloudflare Workers artifacts from the fork.

**Consequences**: This repository becomes simpler and explicitly Docker/NAS
focused. Future Docker image publishing, if needed, is manual/outside-repo
rather than represented by GitHub Actions.

## Out of Scope

* Adding or maintaining GitHub Actions, CircleCI, or Cloudflare Workers.
* Changing compose proxy configuration or scheduler cron behavior.
* Changing Cookie Cloud resolution.
* Adding local persistent state.
* Dumping raw HTML into normal container logs.
* Switching to plain `requests` or adding BeautifulSoup solely to mirror the
  referenced project.

## Technical Notes

* Relevant module: `v2ex/v2ex.py`
* Relevant tests: `tests/test_v2ex.py`
* Research: `research/timerring-cloudcheckin.md`
* Relevant spec: `.trellis/spec/backend/quality-guidelines.md`, scenario
  "V2EX Daily Mission Confirmation"
