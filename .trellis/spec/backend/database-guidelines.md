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
- [cookiecloud/client.py](/home/toph/CloudCheckin/cookiecloud/client.py:1) keeps Cookie Cloud payload handling in process memory instead of introducing local persistence.

---

## Current Storage Model

- Runtime secrets live in environment variables.
- Static platform metadata may live in Python modules or documentation.
- Remote platforms remain the source of truth for check-in state and balances.
- Docker Compose and the long-running scheduler provide orchestration, not durable application storage.

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
- [cookiecloud/client.py](/home/toph/CloudCheckin/cookiecloud/client.py:57) fetches remote JSON and derives control flow directly from the payload.
- [scheduler.py](/home/toph/CloudCheckin/scheduler.py:39) coordinates when the existing platform modules run, but does not introduce any persistent storage.

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
- Keep third-party service configuration explicit, for example `TELEGRAM_TOKEN` and `TELEGRAM_CHAT_ID`.

---

## Common Mistakes

- Do not document imaginary ORM or migration conventions just to fill the template.
- Do not add local persistence for convenience when the feature can derive state from remote responses.
- Do not hardcode cookies, tokens, or chat IDs in source files.
- Do not spread persistence assumptions across scripts; if real storage is introduced later, centralize and document it first.
