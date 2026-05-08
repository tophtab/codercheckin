# Restore Docker image publishing workflow

## Goal

Add a fresh GitHub Actions workflow that builds the repository Docker image and publishes it on pushes to `main`, version tags, and manual dispatch. The immediate problem is that the previous `.github/workflows/dockerhub-publish.yml` was deleted, so GitHub no longer has an active workflow to build the image.

## What I already know

- The user asked to rewrite a Docker workflow.
- The repository currently has no `.github/workflows/` directory on `origin/main`.
- The previous workflow was named `Publish Docker Image` and published to Docker Hub.
- Historical successful Actions runs existed before the workflow deletion.
- `README.md` and Compose defaults use `tophtab/cloudcheckin:latest`.
- `Dockerfile` builds from the repository root and runs `python scheduler.py`.

## Assumptions

- Keep publishing to Docker Hub because the deployment docs use `tophtab/cloudcheckin:latest`.
- Use `secrets.DOCKERHUB_USERNAME` and `secrets.DOCKERHUB_TOKEN` for Docker Hub auth.
- Allow `vars.DOCKERHUB_IMAGE` to override the image name; otherwise default to `<DOCKERHUB_USERNAME>/cloudcheckin`.
- Do not add GHCR publishing unless requested separately.
- GitHub Actions Docker image publishing is part of the intended release path:
  GitHub Actions builds and pushes the Docker Hub image, then the NAS deploys
  by running `docker compose pull` / `docker compose up -d`.

## Requirements

- Add a new workflow under `.github/workflows/`.
- Trigger on:
  - push to `main`
  - tags matching `v*`
  - `workflow_dispatch`
- Build with Docker Buildx from `./Dockerfile` and context `.`.
- Push Docker Hub tags:
  - `latest` on the default branch
  - git SHA tags
  - version tag names for `v*` pushes
- Fail early with a clear message if the required Docker Hub configuration is missing.
- Keep permissions minimal.
- Avoid committing secrets or local environment values.

## Acceptance Criteria

- [ ] A GitHub Actions workflow file exists and is valid YAML.
- [ ] The workflow builds and pushes the Docker image to Docker Hub using maintained official/community Docker actions.
- [ ] Image name resolution is explicit and lowercases the final image name.
- [ ] Manual dispatch can run the same build/publish flow.
- [ ] Local validation checks workflow syntax well enough to catch YAML/action-expression mistakes.

## Definition of Done

- Workflow file added.
- Local syntax validation performed.
- Git status reviewed so unrelated existing changes are not mixed into the explanation.

## Out of Scope

- Changing Dockerfile runtime behavior.
- Changing `docker-compose.yml` or `docker-compose.build.yml`.
- Adding GHCR publishing.
- Creating or rotating Docker Hub secrets.

## Technical Notes

- Previous workflow can be inspected with:
  `git show 2809c77^:.github/workflows/dockerhub-publish.yml`
- Relevant deployment files:
  - `Dockerfile`
  - `docker-compose.yml`
  - `docker-compose.build.yml`
  - `README.md`
- Release contract:
  GitHub Actions publishes the Docker Hub image; Docker Compose on the NAS pulls
  that image and runs it. The workflow must not replace the NAS Compose runtime
  contract.
