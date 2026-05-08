# Add Docker workflow cache

## Goal

Restore BuildKit GitHub Actions cache usage in the Docker Hub publishing workflow so repeated image builds can reuse Docker layers and avoid unnecessary cold builds.

## What I already know

- The current Docker workflow succeeds but the latest run took about 40 seconds.
- The `Build and push Docker image` step increased from about 9 seconds in the old workflow to about 21 seconds in the rewritten workflow.
- The old workflow used `cache-from: type=gha` and `cache-to: type=gha,mode=max`.
- The project release path is GitHub Actions builds/pushes the Docker Hub image, then NAS updates with `docker compose pull` / `docker compose up -d`.

## Requirements

- Add BuildKit GHA cache settings back to `.github/workflows/dockerhub-publish.yml`.
- Keep the existing Docker Hub image resolution, triggers, tags, and minimal permissions unchanged.
- Do not touch Dockerfile, Compose files, or unrelated dirty files.

## Acceptance Criteria

- [ ] `docker/build-push-action@v6` has `cache-from: type=gha`.
- [ ] `docker/build-push-action@v6` has `cache-to: type=gha,mode=max`.
- [ ] Workflow lint passes locally.

## Definition of Done

- Workflow updated.
- `actionlint` or equivalent workflow validation passes.
- Change is committed and pushed.

## Out of Scope

- Changing image tags.
- Changing Dockerfile layer structure.
- Changing Docker Hub secrets or repo variables.
