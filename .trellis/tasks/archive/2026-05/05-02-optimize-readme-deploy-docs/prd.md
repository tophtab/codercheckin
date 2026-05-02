# 优化 README 部署说明

## Goal

Improve the README so deployment guidance is easier to copy and use, with a complete Docker Compose configuration placed near the top of the document.

## Requirements

* Put a copy-ready Docker Compose example near the beginning of `README.md`.
* Keep the README as concise as possible while preserving deployment essentials.
* Keep the README in Chinese, matching the current audience and style.
* Preserve concise guidance for Cookie Cloud, manual cookies, Telegram, cron, target selection, logs, and local development.
* Avoid changing runtime behavior or source code.

## Acceptance Criteria

* [x] `README.md` includes a complete `compose.yaml` / Docker Compose block before the longer feature and FAQ sections.
* [x] The quick-start flow tells users how to create `.env`, start the container, and view logs.
* [x] Verbose logs, long FAQ, feature marketing, project structure, and tech stack sections are removed.
* [x] Existing compose variable names remain aligned with `docker-compose.yml`.
* [x] No application code is changed.

## Definition of Done

* Documentation updated.
* Git diff reviewed.
* No tests required because this is README-only.

## Technical Notes

* Inspected `README.md`, `docker-compose.yml`, and `docker-compose.build.yml`.
* Existing runtime compose file uses `tophtab/cloudcheckin:latest` via `CLOUDCHECKIN_IMAGE`, `.env`, `CHECKIN_TARGETS`, `CHECKIN_CRON`, `PYTHONUNBUFFERED`, and `TZ`.
* Final review found no new implementation contract or reusable coding convention that needs a `.trellis/spec/` update.
