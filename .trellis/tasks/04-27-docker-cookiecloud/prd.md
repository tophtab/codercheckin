# Docker support with Cookie Cloud

## Goal
Add self-hosted Docker deployment support for this repository and integrate an optional Cookie Cloud cookie source without breaking the existing environment-variable-based workflow.

## Requirements
- Add Docker artifacts so the project can run on a NAS with a container-based deployment flow.
- Keep the original per-platform Python modules and direct cookie environment variables working as they do now.
- Add an optional Cookie Cloud integration that can download and resolve cookies for supported platforms when direct cookie environment variables are not set.
- Document the new deployment and configuration flow in Chinese and English READMEs.

## Acceptance Criteria
- [ ] The repository includes a `Dockerfile` and a `docker-compose.yml` for local or NAS deployment.
- [ ] A container entrypoint can run one or more existing platform modules without requiring code changes by the operator.
- [ ] `NODESEEK_COOKIE`, `DEEPFLOOD_COOKIE`, `V2EX_COOKIE`, and `ONEPOINT3ACRES_COOKIE` still work as first-priority configuration.
- [ ] Cookie Cloud can provide cookies for Nodeseek, Deepflood, V2EX, and 1Point3Acres when its required configuration is present.
- [ ] The environment template and README files document the Docker and Cookie Cloud setup clearly.

## Technical Notes
- Use Cookie Cloud's `/get/:uuid` API with `password` to request decrypted cookie payloads.
- Keep secrets in environment variables only.
- Prefer a lightweight shared helper instead of introducing a larger abstraction layer.
