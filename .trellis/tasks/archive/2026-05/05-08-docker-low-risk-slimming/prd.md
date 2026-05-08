# Low-risk Docker image slimming

## Goal

Reduce the CloudCheckin Docker image size with only low-risk build-time changes, without changing runtime behavior, Compose usage, base image family, dependencies, scheduler behavior, or application code.

## What I already know

* The user wants the low-risk image slimming option only.
* Current `Dockerfile` uses `python:3.11-slim`, copies `requirements.txt`, upgrades pip, installs dependencies, copies app files, and runs `python scheduler.py`.
* Prior local audit showed removing `pip install --upgrade pip` and disabling/cleaning bytecode reduced local image size from about 298MB to about 266MB.
* Runtime memory optimization is not in scope; the current always-on scheduler remains the preferred no-extra-configuration deployment model.

## Requirements

* Remove the runtime-unneeded pip upgrade step from the Docker image build.
* Install Python dependencies with `--no-cache-dir --no-compile`.
* Clean generated Python bytecode/cache files from `/usr/local/lib/python3.11` during the dependency install layer.
* Keep the existing base image, working directory, copy behavior, and `CMD ["python", "scheduler.py"]`.
* Do not change Compose files, Python application code, dependencies, or scheduling behavior.

## Acceptance Criteria

* [ ] `Dockerfile` contains the low-risk dependency install changes.
* [ ] The image builds successfully from the repository root.
* [ ] A container can start the scheduler with placeholder cookie configuration and reach the waiting-for-next-run state.
* [ ] No unrelated files are changed except Trellis task metadata/context files.

## Out of Scope

* Switching to Alpine, distroless, scratch, Go, or Rust.
* Removing `curl_cffi`, `cryptography`, certificates, timezone data, or other runtime dependencies.
* Changing runtime memory behavior or replacing the internal scheduler.

## Technical Notes

* Relevant file: `Dockerfile`.
* Relevant spec context: `.trellis/spec/backend/index.md`.
