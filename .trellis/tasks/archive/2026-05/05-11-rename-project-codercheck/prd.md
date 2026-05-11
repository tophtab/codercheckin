# Rename Project To codercheckin

## Goal

Rename this fork from CloudCheckin/cloudcheckin to codercheckin, and remove the uppercase local folder name because the current directory casing is uncomfortable to work with.

## What I Already Know

* User wants the project renamed to `codercheckin`.
* User explicitly prefers no uppercase letters in the folder name.
* Existing references found in `README.md`, `pyproject.toml`, Docker Compose files, `.env.localtest.example`, `config.py`, and the Git remote URL.
* The repo has unrelated uncommitted Trellis changes already present; they must not be reverted or included as part of this rename.

## Requirements

* Rename project/package identity from `cloudcheckin`/`CloudCheckin` to `codercheckin`.
* Update Docker service names, Docker image defaults, and matching environment variable names to use `codercheckin`.
* Update README usage examples, clone URL, and local directory examples to use lowercase `codercheckin`.
* Update source comments/docstrings that describe the project name.
* Rename the local checkout folder from `/home/toph/CloudCheckin` to `/home/toph/codercheckin` after tracked file edits are complete.
* Preserve domain-specific terms such as `checkin`, `CHECKIN_TARGETS`, and module/function names that describe actual sign-in behavior.

## Acceptance Criteria

* [x] `rg -n "CloudCheckin|cloudcheckin|cloud-checkin|Cloud Checkin|Cloud CheckIn"` finds no stale project-name references in non-Trellis project files.
* [x] `pyproject.toml` project name is `codercheckin`.
* [x] Docker Compose service and image defaults use `codercheckin`.
* [x] README title and setup snippets use `codercheckin`.
* [x] Tests pass after the rename.
* [x] Local folder path is lowercase `/home/toph/codercheckin`.

## Definition Of Done

* Tests pass for the existing suite.
* No unrelated dirty files are reverted.
* Trellis task artifacts record the rename decision.

## Technical Approach

Apply a targeted text/config rename for project identity references only. Do not rename Python modules such as `checkin_runner.py` or environment variables such as `CHECKIN_TARGETS`, because those describe check-in behavior rather than the product name.

## Out Of Scope

* Changing Python module names or public behavior.
* Pushing changes to a remote repository.
* Renaming the GitHub repository through GitHub APIs.
* Rewriting unrelated Trellis WIP that predates this task.

## Technical Notes

* Inspected `README.md`, `pyproject.toml`, `docker-compose.yml`, `docker-compose.build.yml`, `.env.localtest.example`, and `config.py`.
* Existing remote is `https://github.com/tophtab/CloudCheckin.git`; this task may update the local remote URL if a predictable `codercheckin` URL is appropriate, but it will not contact GitHub or rename the hosted repo.
