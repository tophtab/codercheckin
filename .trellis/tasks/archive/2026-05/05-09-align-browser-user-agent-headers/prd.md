# Align browser user agent headers

## Goal

Update CloudCheckin's browser identity headers to match the user's primary browser UA so cookie-backed check-ins, especially V2EX, are less likely to present mismatched browser metadata.

## What I already know

* User's primary browser UA is `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36`.
* `config.py` defines a shared `DEFAULT_USER_AGENT` currently set to Windows Edge/Chrome 125.
* `attendance_checkin.py` uses `DEFAULT_USER_AGENT` for shared Nodeseek/Deepflood-style check-ins.
* `v2ex/v2ex.py` hardcodes a separate macOS Chrome 142 UA and matching `sec-ch-ua` / `sec-ch-ua-platform` values.
* User provided current browser request headers for Nodeseek, Deepflood, and V2EX. The stable browser identity values worth reusing are `accept-language: zh-CN,zh;q=0.9` and Chrome 132 UA/client hints. Captured request-only values should not be copied blindly.
* Upstream `timerring/CloudCheckin` Python scripts use only `User-Agent`, `Origin`, `Referer`, `Content-Type`, and `Cookie` for Nodeseek/Deepflood. Its V2EX Python script uses fuller navigation headers, including `accept`, `accept-language`, `sec-ch-ua`, platform hints, fetch metadata, upgrade, UA, and cookie.

## Assumptions

* The supplied UA should become the default browser UA for this repo.
* V2EX headers should stay internally consistent with the supplied UA by using Chrome/Chromium 132 and Windows platform client hints.
* Dynamic, secret, or request-context-specific values such as cookies, Cloudflare clearance cookies, `refract-key`, `refract-sign`, DNT, and GPC must not be hardcoded unless the actual check-in endpoint requires them.
* `accept-encoding` should be left to the HTTP client rather than manually pinned.

## Requirements

* Replace the shared default UA with the supplied Windows Chrome 132 UA.
* Make V2EX use the shared default UA instead of duplicating a separate UA string.
* Update V2EX client hints to match Chrome/Chromium 132 on Windows.
* Add stable browser identity headers where appropriate: Chinese accept-language and V2EX Chrome client hints.
* Keep cookies, tokens, and other secret-bearing configuration out of source.
* Add or update focused tests for the header contract.

## Acceptance Criteria

* [ ] `attendance_checkin.py` continues to get its UA from `DEFAULT_USER_AGENT`.
* [ ] `v2ex.build_headers()` returns the supplied UA.
* [ ] `v2ex.build_headers()` returns `sec-ch-ua` values for Chrome/Chromium 132 and `sec-ch-ua-platform` as `"Windows"`.
* [ ] Shared attendance headers include stable browser identity headers without hardcoding dynamic request signature values or unrelated privacy preference headers.
* [ ] Relevant tests pass.

## Definition of Done

* Tests added/updated where appropriate.
* Lint/typecheck or focused test commands run successfully.
* No unrelated behavior changes.

## Out of Scope

* Capturing or storing cookies, tokens, or full browser fingerprints.
* Hardcoding `refract-key`, `refract-sign`, `cf_clearance`, or other per-session request data.
* Changing V2EX request flow, session handling, or check-in parsing.
* Adding runtime UA configuration via environment variable.

## Technical Notes

* A tiny shared constant is preferable to keeping divergent hardcoded UA strings.
* Nodeseek and Deepflood browser samples include service-worker/refract headers. Those values appear dynamic and should remain outside source code unless the check-in flow explicitly implements their generation.
