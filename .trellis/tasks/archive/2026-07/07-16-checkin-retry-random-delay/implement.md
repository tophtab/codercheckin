# Implementation Plan

1. Add centralized constants for three total attempts, a 30-second retry
   interval, and an inclusive 0–1800 second scheduled-run delay.
2. Refactor `checkin_runner.run_targets` so each target attempt uses the existing
   subprocess/output helpers and retries independently before recording an
   exhausted failure.
3. Add injectable `sleep` behavior to the target runner and cover success,
   recovery, exhausted retries, start failures, ordering, and aggregate errors.
4. Add an injectable scheduler helper that selects, logs, and sleeps for the
   random post-cron delay.
5. Invoke the random-delay helper once after each cron wait and before the
   scheduled-run start log.
6. Update scheduler tests for zero and maximum delay boundaries and invocation
   ordering without real sleeping.
7. Update deployment documentation to describe the fixed retry and random-delay
   behavior.
8. Run the complete pytest suite and `docker compose config`.

## Risk and Rollback

- Risk: retrying a deterministic authentication failure increases run duration;
  bounded attempts limit the impact.
- Risk: careless retry placement could rerun successful targets; tests must
  assert per-target call order explicitly.
- Rollback: revert the runner loop and scheduler delay call; no persistent data
  or configuration migration is involved.
