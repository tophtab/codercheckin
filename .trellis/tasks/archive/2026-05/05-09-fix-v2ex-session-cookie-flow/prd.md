# Fix V2EX Session Cookie Flow

## Goal

Make the Docker/NAS V2EX daily mission flow preserve cookies issued during the
mission page and redeem requests, matching browser behavior so the first daily
check-in attempt succeeds.

## What I Already Know

* On 2026-05-09, the NAS container successfully loaded `V2EX_COOKIE` from
  Cookie Cloud and reached authenticated V2EX pages.
* The static-header flow loaded `/mission/daily`, parsed a redeem action, and
  received `302 Location: /mission/daily` from redeem, but the page still
  produced a new redeem action afterward.
* A live diagnostic using `curl_cffi.requests.Session()` with a cookie jar
  preserved V2EX `Set-Cookie` values and completed the check-in. The follow-up
  mission page showed `/balance` and `每日登录奖励已领取`.
* The existing implementation uses `curl_cffi` and finite timeouts and must keep
  token-bearing `once` values out of normal logs.

## Requirements

* V2EX requests in a single run must share a `curl_cffi.requests.Session()` so
  cookies set by `/mission/daily` and redeem are sent to later requests.
* The session must be initialized from the resolved `V2EX_COOKIE` value,
  including Cookie Cloud values.
* Existing public behavior should remain stable: already-signed states succeed,
  login pages fail clearly, unsupported actions fail clearly, and Telegram
  notification behavior remains unchanged.
* Continue to confirm successful redeem through today's `/balance`
  `每日登录奖励` entry.
* Do not log cookies, full authenticated headers, redeem URLs, or `once` tokens.

## Acceptance Criteria

* [x] A first-run V2EX redeem path uses one shared session across mission,
      redeem, and balance confirmation requests.
* [x] Unit tests cover that cookies issued by the mission request are available
      to the redeem request.
* [x] Existing V2EX tests still pass.
* [x] Full project tests pass.

## Out of Scope

* Changing the V2EX TLS/browser impersonation strategy.
* Changing Cookie Cloud matching behavior.
* Changing scheduler, Docker image, or Telegram configuration behavior.

## Technical Notes

* Main module: `v2ex/v2ex.py`
* Focused tests: `tests/test_v2ex.py`
* Relevant spec: `.trellis/spec/backend/quality-guidelines.md` section
  "V2EX Daily Mission Confirmation"
* Live NAS evidence: static `cookie` header failed; `requests.Session()` with a
  populated cookie jar succeeded and incremented the account balance.
