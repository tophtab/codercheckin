# Quality Guidelines

> Code quality standards for backend development.

---

## Overview

This repository is a lightweight automation project. Quality here means:

- the scripts continue to match each platform's real behavior
- secrets stay in environment variables
- failures are obvious in CI logs
- shared logic is reused instead of cloned carelessly
- local debug commands from the README still work

The codebase is pragmatic rather than heavily abstracted. Follow existing shapes
unless there is a clear maintenance problem to solve.

---

## Forbidden Patterns

- Do not hardcode cookies, tokens, chat IDs, or webhook URLs in source files.
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
- Environment validation in [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:183).
- Local debug execution commands in [README.md](/home/toph/CloudCheckin/README.md:153).

---

## Testing Requirements

There is no automated test suite in the repository today.
That is current reality and the documentation should reflect it honestly.

Minimum verification for backend changes:

- Run the affected module locally with `python -m ...` when possible.
- Confirm required environment variables are documented or preserved.
- For parsing changes, verify against a real response sample or the live platform when safe.
- For Worker changes, verify with `wrangler` local/dev tooling or a targeted deployed test if available.

If you add a non-trivial parsing helper, retry policy, or shared utility, prefer to
add isolated tests rather than expanding the current manual-only model further.

---

## Code Review Checklist

- Does the change match the existing package-per-platform structure?
- Are secrets still sourced only from environment variables?
- Are failure paths visible through stdout or Worker logs and, when appropriate, Telegram?
- Did the author reuse existing notification or captcha integration code where applicable?
- If a constant or endpoint changed, were all platform-specific copies searched first?
- Does the README or operational documentation need updating because local setup or secrets changed?

---

## Common Mistakes

- Adding a feature for one platform by copying another script and forgetting to rename environment variables or notification text.
- Logging too little to debug CI failures, or too much sensitive data.
- Changing an external request header or regex in one place without checking related Worker or Python variants.
- Treating this project like a generic backend service and adding abstractions that make simple automation harder to trace.
