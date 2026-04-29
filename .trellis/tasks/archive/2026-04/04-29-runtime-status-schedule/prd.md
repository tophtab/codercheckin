# Fix Runtime Status Display and Schedule Time

## Goal

Make the Docker scheduler and platform runner logs readable enough to diagnose daily check-in status, and change the default automatic run time from 03:00 to 03:30 Asia/Shanghai.

## What I Already Know

* The user observed only the scheduler startup and next scheduled time in logs after running for a day.
* `scheduler.py` currently logs startup and the next run, then sleeps silently until the scheduled time.
* If the container starts after the day's cron time, croniter schedules the next run for the following day.
* The default cron value appears in `scheduler.py`, `docker-compose.yml`, and `README.md`.
* The user specifically expects platform-level check-in status for targets such as V2EX, including whether each target succeeded or failed.
* The current scheduler next-run timestamp uses raw ISO format, which is correct but hard to read in logs.
* The user also needs failing target logs to include the actual error/output text, not only an exit code.

## Requirements

* Default scheduled check-in time is 03:30.
* Container logs show ongoing waiting status after startup instead of going silent until the next run.
* Existing scheduled check-in execution order is preserved, but failure propagation should raise an error message that includes the target's recent output instead of only returning an exit code.
* Documentation matches the new default schedule and log behavior.
* Each configured platform target logs a clear start line and a clear success or failure line.
* Scheduler timestamps use a human-readable local format in startup, next-run, wait, start, finish, and failure logs.
* When a platform subprocess fails, the runner logs enough recent stdout/stderr text to show which step failed and what error string was emitted.
* When a platform subprocess fails, the scheduler process should raise an exception whose message includes the failing target and recent error/output text.

## Acceptance Criteria

* [x] Default cron config is `30 3 * * *`.
* [x] The scheduler emits periodic wait status logs before the next run.
* [x] README examples show the new default 03:30 schedule.
* [x] Targeted scheduler tests pass.
* [x] Platform target logs show success or failure for each target.
* [x] Scheduler next-run and wait-status timestamps are easier to read than raw ISO strings.
* [x] Tests cover platform target result logs and readable scheduler timestamps.
* [x] Failing platform target logs include the recent error/output text from that target subprocess.
* [x] Tests cover subprocess output forwarding and failure summaries.
* [x] Tests cover raised failure messages that include the failing target and recent output text.

## Out of Scope

* Changing platform check-in network logic.
* Changing Telegram notification behavior.
* Running a live check-in with real credentials.

## Technical Notes

* Relevant files inspected: `scheduler.py`, `checkin_runner.py`, `docker-compose.yml`, `README.md`, `tests/test_checkin_runner.py`, `tests/test_scheduler.py`.
* Relevant specs read: backend quality, logging, error handling, and code reuse thinking guide.
