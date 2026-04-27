# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

This repository currently has no database, no ORM, no migrations, and no local
data persistence layer.

The backend behavior is request-driven:

- read secrets from environment variables
- call remote platform APIs or HTML pages
- parse the response
- send Telegram notifications
- exit with a failure code when the automation fails

That means database guidance for this project is mostly about not inventing one
where none exists, and about being explicit if future work introduces state.

Examples of the current pattern:

- [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:21) keeps state in process memory only.
- [nodeseek/nodeseek.py](/home/toph/CloudCheckin/nodeseek/nodeseek.py:9) reads cookies from environment variables and immediately performs remote requests.
- [onepoint3acres/questions.py](/home/toph/CloudCheckin/onepoint3acres/questions.py:1) stores static answer data in source control instead of a database.

---

## Current Storage Model

- Runtime secrets live in environment variables.
- Static platform metadata may live in Python modules or documentation.
- Remote platforms remain the source of truth for check-in state and balances.
- Cloudflare and CircleCI provide orchestration, not durable application storage.

If you need to remember state between runs, first ask whether the remote platform
already exposes enough information to avoid local persistence.

---

## Query Patterns

There are no local queries in this repository.

Instead, backend modules follow these patterns:

- Use HTTP requests to fetch current remote state.
- Parse HTML or JSON inline in the platform module.
- Derive control flow directly from the response body.

Examples:

- [v2ex/v2ex.py](/home/toph/CloudCheckin/v2ex/v2ex.py:31) parses the daily mission page with regular expressions.
- [onepoint3acres/onepoint3acres.py](/home/toph/CloudCheckin/onepoint3acres/onepoint3acres.py:65) fetches question data and reads the JSON payload directly.
- [cloudflareworkers/src/v2ex.js](/home/toph/CloudCheckin/cloudflareworkers/src/v2ex.js:133) fetches remote pages inside the Worker and extracts response data with string checks and regex.

---

## Migrations

There is no migration system today.

If future work introduces a database or other persistent storage, do not hide it
inside an existing script. The first change must also add documented guidance for:

- chosen storage technology
- schema ownership
- migration workflow
- rollback strategy
- local development setup

Until then, keep state changes external to the repository runtime.

---

## Naming Conventions

Because there is no schema, naming conventions focus on configuration keys.

- Use explicit environment variable names in `UPPER_SNAKE_CASE`.
- Prefer platform-prefixed names such as `V2EX_COOKIE` and `DEEPFLOOD_COOKIE`.
- Keep third-party service configuration explicit, for example `TWOCAPTCHA_APIKEY`, `TELEGRAM_TOKEN`, and `TELEGRAM_CHAT_ID`.

---

## Common Mistakes

- Do not document imaginary ORM or migration conventions just to fill the template.
- Do not add local persistence for convenience when the feature can derive state from remote responses.
- Do not hardcode cookies, tokens, or chat IDs in source files.
- Do not spread persistence assumptions across scripts; if real storage is introduced later, centralize and document it first.
