# Audit Docker build context and ignores

## Goal

Prevent development, agent, test, cache, virtualenv, and potentially sensitive local files from being copied into the Docker image. The running container should contain only the application code and runtime files needed by `scheduler.py`.

## What I already know

* The user found unrelated directories in the Docker container, including agent tooling, Codex tooling, Cloud-related local files, and test files.
* `Dockerfile` currently uses `COPY . .`, so everything not excluded by `.dockerignore` is copied into `/app`.
* Current `.dockerignore` excludes `.env`, `.git`, `.github`, `.trellis`, Python bytecode, and `node_modules`, but does not exclude `.agents`, `.codex`, `.claude`, `.cursor`, `.venv`, `.pytest_cache`, `tests`, packaging metadata, or local compose/dev files.
* `tests/` is useful for development and CI, but it is not needed inside the runtime container.

## Assumptions

* Keep the existing Dockerfile shape for now and solve this by tightening `.dockerignore`.
* Do not remove tests or agent configuration from the repository; only keep them out of Docker builds.
* Preserve runtime source packages and files required by `scheduler.py`.

## Requirements

* Update Docker ignore rules so Docker build context excludes:
  * agent/editor/tooling directories such as `.agents`, `.codex`, `.claude`, and `.cursor`
  * Trellis and CI metadata
  * local virtualenvs, Python caches, pytest caches, and packaging build artifacts
  * test-only files and directories
  * local environment and compose/build helper files not needed in the image
* Keep application runtime files available to the image.
* Verify that ignored paths are not present in the effective Docker build context or image contents.
* Audit repository-local directories and decide whether they should be deleted, git-ignored, or kept:
  * keep source files and development tests that protect behavior
  * delete local generated/cache artifacts that are safe to regenerate
  * add missing `.gitignore` rules for generated/cache artifacts that should not be committed
  * do not delete local secrets or workflow configuration without a clear reason

## Acceptance Criteria

* [ ] `.dockerignore` excludes the listed non-runtime directories and sensitive local files.
* [ ] `.gitignore` excludes generated/cache artifacts that should not be tracked.
* [ ] Safe local generated/cache directories are removed from the working tree.
* [ ] `tests/` remains in the repository unless a replacement quality gate is provided.
* [ ] Docker build succeeds.
* [ ] Built image does not contain `.agents`, `.codex`, `.claude`, `.cursor`, `.trellis`, `.venv`, `.pytest_cache`, `tests`, or `.env`.
* [ ] Project lint/type-check/test command, if available, still passes or any unavailable command is clearly noted.

## Definition of Done

* Focused Docker ignore change committed to the working tree.
* Verification commands run and results documented in the final response.
* No unrelated repository files removed or reverted.

## Out of Scope

* Restructuring the Dockerfile into a whitelist-copy Dockerfile.
* Removing test files from the source repository.
* Changing application runtime behavior.

## Technical Notes

* Inspected: `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `docker-compose.build.yml`, and top-level repository directories.
* Root cause: `COPY . .` combined with incomplete `.dockerignore`.
