# Update Docker Hub Image Name

## Goal

Ensure the Docker Hub image published by the GitHub Actions workflow uses the renamed project image name, `codercheckin`, instead of the old `cloudcheckin` fallback.

## What I Already Know

* The user reported that the Docker image built in the workflow and uploaded to Docker Hub appears not to have switched to the new name.
* Existing Compose and README references use `tophtab/codercheckin:latest`.
* `.github/workflows/dockerhub-publish.yml` still falls back to `$DOCKERHUB_USERNAME/cloudcheckin` when `vars.DOCKERHUB_IMAGE` is unset.
* `vars.DOCKERHUB_IMAGE`, if configured in GitHub repository settings, still overrides the fallback.

## Requirements

* Update the Docker Hub publish workflow fallback image name from `cloudcheckin` to `codercheckin`.
* Keep the existing `vars.DOCKERHUB_IMAGE` override behavior intact.
* Do not change Compose runtime image references unless another stale image name is found.

## Acceptance Criteria

* [x] `.github/workflows/dockerhub-publish.yml` defaults to `$DOCKERHUB_USERNAME/codercheckin`.
* [x] No runtime or publish configuration references to the old `cloudcheckin` image name remain.
* [x] YAML syntax remains valid.

## Definition of Done

* Lint/typecheck or a targeted validation is run where appropriate.
* The final response calls out that a GitHub repository variable named `DOCKERHUB_IMAGE`, if set to the old name, must also be updated in repo settings.

## Technical Approach

Make a scoped workflow edit to the fallback image name and verify by searching for stale `cloudcheckin` references.

## Decision

**Context**: The project was renamed to `codercheckin`, but the Docker Hub workflow retained the previous image fallback.

**Decision**: Change only the fallback value to `"$DOCKERHUB_USERNAME/codercheckin"` while preserving explicit repository variable overrides.

**Consequences**: Repositories that set `vars.DOCKERHUB_IMAGE` continue to control the published image name manually; local code cannot update that remote setting.

## Out of Scope

* Changing Docker Hub repository settings or GitHub repository variables remotely.
* Renaming service names or Compose environment variable names.

## Technical Notes

* Inspected `.github/workflows/dockerhub-publish.yml`, `docker-compose.yml`, `docker-compose.build.yml`, and `.trellis/spec/backend/index.md`.
* Relevant stale value: `image_name="$DOCKERHUB_USERNAME/cloudcheckin"`.
