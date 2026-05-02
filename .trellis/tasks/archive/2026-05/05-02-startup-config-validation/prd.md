# Startup Config Validation

## Goal

Validate cookie configuration when the Docker scheduler starts so operators can tell immediately whether the configured targets are runnable instead of waiting until the first scheduled check-in.

## What I already know

- Docker runs `python scheduler.py` by default.
- `CHECKIN_TARGETS` selects enabled platforms and currently defaults to `nodeseek,deepflood,v2ex`.
- Direct cookie environment variables are `NODESEEK_COOKIE`, `DEEPFLOOD_COOKIE`, and `V2EX_COOKIE`.
- Cookie Cloud is optional fallback when a direct platform cookie is empty.
- Existing cookie resolution is centralized in `cookiecloud.client.get_cookie_value(env_name, domains)`.
- Cookie Cloud requests already use a finite timeout and print safe failure messages.
- Logs must not print full cookies, tokens, Cookie Cloud password, or request headers.

## Assumptions

- Startup validation should fail fast and exit non-zero if any enabled target has no usable direct cookie and no matching Cookie Cloud cookie.
- A direct cookie counts as valid for startup if the configured environment value is non-empty after trimming. Full login validity is still checked during actual sign-in.
- A Cookie Cloud cookie counts as valid if Cookie Cloud can be reached/decrypted and returns matching cookies for the target domains.

## Requirements

- Validate enabled targets once during scheduler startup, after parsing `CHECKIN_TARGETS` and before entering the wait loop.
- For each enabled target, check whether a direct cookie is configured.
- If no direct cookie is configured, attempt Cookie Cloud fallback and verify it can produce a cookie for the target's domains.
- Print safe startup validation logs showing target name and source (`environment` or `Cookie Cloud`) without printing secret values.
- If validation fails for any enabled target, print enough context to identify the failed target and exit non-zero before scheduling begins.
- Preserve the current runtime behavior for actual check-in execution.

## Acceptance Criteria

- [x] Scheduler startup logs a successful validation message before waiting for the next run when all enabled targets have direct cookies or Cookie Cloud matches.
- [x] Scheduler exits non-zero before the wait loop when an enabled target lacks both direct cookie and Cookie Cloud match.
- [x] Cookie Cloud failures during startup are visible in container logs.
- [x] Startup validation does not log raw cookie strings, Telegram tokens, Cookie Cloud password, or full auth headers.
- [x] Unit tests cover direct cookie success, Cookie Cloud success, missing cookie failure, and scheduler integration.

## Definition of Done

- Tests added/updated for the new validation behavior.
- Lint/typecheck or the project equivalent is run.
- Documentation updated if user-facing Docker startup behavior changes.
- Spec update considered after implementation.

## Out of Scope

- Verifying that a cookie is still accepted by the destination website before check-in.
- Changing the `.env`/`env_file` configuration model.
- Adding Docker/Kubernetes secrets support.
- Sending Telegram notifications for startup validation failures.

## Technical Notes

- Relevant files inspected: `scheduler.py`, `checkin_runner.py`, `cookiecloud/client.py`, `attendance_checkin.py`, `nodeseek/nodeseek.py`, `deepflood/deepflood.py`, `v2ex/v2ex.py`.
- Backend specs relevant to this task: `.trellis/spec/backend/error-handling.md`, `.trellis/spec/backend/quality-guidelines.md`, `.trellis/spec/backend/logging-guidelines.md`.
