# Pin curl_cffi Version

## Goal

Make Docker builds reproducible and prevent unreviewed `curl_cffi` upgrades from
changing the native TLS stack used by the V2EX integration.

## Background

- The failed V2EX run loaded its cookie successfully but failed during the TLS
  handshake with curl error 35 and `OPENSSL_internal:invalid library`.
- Both `requirements.txt` and `pyproject.toml` currently declare `curl_cffi`
  without a version constraint.
- Repository history contains no previously pinned or documented known-good
  version.
- `curl_cffi==0.15.0` installs successfully but reproduces the reported TLS
  error inside the project's `python:3.11-slim` Docker base image.
- A direct request to `https://www.v2ex.com/mission/daily` using
  `curl_cffi==0.14.0`, the same Docker base image, and browser impersonation
  returned HTTP 200 on 2026-07-16.

## Requirements

- Pin `curl_cffi` to exactly `0.14.0` in every production dependency manifest.
- Keep `requirements.txt` and `pyproject.toml` consistent.
- Do not change V2EX request behavior, Cookie Cloud handling, or scheduler flow.
- Keep the exact dependency constraint explicit in both production manifests.

## Acceptance Criteria

- [x] `requirements.txt` installs exactly `curl_cffi==0.14.0`.
- [x] `pyproject.toml` declares exactly `curl_cffi==0.14.0`.
- [x] Automated tests pass.
- [x] Manual verification confirms both manifests use the same pin.
- [x] The Docker image can still install the declared dependencies.

## Out of Scope

- Adding a fallback HTTP client.
- Diagnosing platform-specific NAS TLS failures beyond making the installed
  dependency version deterministic.
- Changing other dependency versions.
