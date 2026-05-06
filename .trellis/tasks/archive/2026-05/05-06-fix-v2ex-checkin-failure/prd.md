# fix: V2EX check-in failure

## Goal

Restore reliable V2EX scheduled check-in when `V2EX_COOKIE` is resolved from Cookie Cloud, and make future V2EX failures diagnosable from Docker logs without exposing cookie values.

## What I already know

- The scheduled run on 2026-05-06 loaded `V2EX_COOKIE` from Cookie Cloud, then failed with only `Fail to check in` in stdout.
- Nodeseek and DeepFlood succeeded in the same run, so the scheduler, Cookie Cloud decryption, and target runner were generally working.
- Upstream `timerring/CloudCheckin` V2EX still reads a manually supplied `V2EX_COOKIE` and uses the same basic `/mission/daily` then `/mission/daily/redeem?once=...` flow.
- This repo added Cookie Cloud fallback, import-safe platform modules, timeouts, and timestamped logs around the upstream V2EX flow.
- The current Cookie Cloud resolver merges matched host cookies by cookie name, which can drop a host-specific V2EX cookie when `v2ex.com` and `www.v2ex.com` contain duplicate names.
- V2EX's unauthenticated daily page currently renders an English sign-in page with `You need to sign in first to view this page`, so checking only the Chinese `需要先登录` text is not enough for diagnostics.
- A live redacted comparison showed Cookie Cloud and a manually copied browser cookie have matching `A2` and `PB3_SESSION` values; Cookie Cloud omits `V2EX_LANG` and has a different `V2EX_TAB`, neither of which appears to block access to the daily mission page.
- Both Cookie Cloud and manually copied cookie headers can load `https://www.v2ex.com/mission/daily` and parse a `redeem?once=...` token.
- `build_headers()` preserves a quoted cookie header string containing semicolons and pipe characters, so the Python parameter passing path is not truncating the cookie.
- Live validation on 2026-05-06 09:10 Asia/Shanghai: running `python3 -m v2ex.v2ex` with Cookie Cloud credentials completed V2EX check-in; the V2EX balance page recorded `20260506` daily reward at `09:10:46 +08:00`.

## Requirements

- Preserve the upstream V2EX request flow unless a local integration bug is identified.
- Keep direct `V2EX_COOKIE` as first priority; only use Cookie Cloud when the direct env var is empty.
- Build Cookie Cloud cookie headers in a way that avoids unrelated subdomain cookies and prefers the most specific matching host for duplicate cookie names.
- Do not log raw cookies, tokens, request headers, or HTML responses.
- Log safe V2EX failure context so Docker/NAS logs identify whether the job failed because the cookie was unauthenticated, the once token could not be parsed, redeem failed, or balance parsing failed.
- Treat V2EX's post-redeem "already claimed" daily-mission state as a successful/idempotent outcome when it appears immediately after a redeem request.
- Preserve import safety for platform modules.

## Acceptance Criteria

- [x] Unit tests cover Cookie Cloud duplicate-name handling across `v2ex.com` and `www.v2ex.com`.
- [x] Unit tests cover avoiding unrelated subdomain cookies.
- [x] Unit tests cover V2EX login-page detection in both Chinese and English variants.
- [x] `python3 -m compileall` passes for affected modules.
- [x] Relevant pytest tests pass.

## Out of Scope

- Storing, printing, or inspecting real user cookies.
- Changing V2EX check-in endpoints beyond compatibility diagnostics.
- Adding a new notification provider.

## Technical Notes

- Upstream source checked: https://github.com/timerring/CloudCheckin/blob/main/v2ex/v2ex.py
- Relevant local files: `v2ex/v2ex.py`, `cookiecloud/client.py`, `tests/test_cookiecloud_client.py`.
- Relevant specs: `.trellis/spec/backend/quality-guidelines.md`, `.trellis/spec/backend/error-handling.md`, `.trellis/spec/backend/logging-guidelines.md`.
