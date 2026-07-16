# Design: Check-in Retries and Random Schedule Delay

## Architecture and Boundaries

The scheduler owns the run-level random delay because it is triggered once per
cron occurrence. The target runner owns retry behavior because it already owns
target subprocess lifecycle, output forwarding, ordering, and aggregate failure
reporting.

## Scheduler Flow

1. Resolve the next cron occurrence and wait until it.
2. Generate one inclusive random delay from 0 through 1800 seconds.
3. Log the selected delay.
4. Sleep for that delay, including zero as an immediate start.
5. Start the scheduled target run.

Random generation and sleeping remain injectable for deterministic tests. The
delay is selected independently for every cron occurrence and is not added to
the calculation of the following cron occurrence.

## Target Retry Flow

For each configured target, in the existing order:

1. Start attempt 1.
2. On success, log success and move to the next target.
3. On a non-zero exit or subprocess start failure, capture and log the failure.
4. If fewer than three attempts have run, log the upcoming retry, wait 30
   seconds, and retry the same target.
5. After attempt 3 fails, retain only the final attempt's bounded recent output
   in the target failure and move to the next target.
6. After every target has been processed, raise the existing single or aggregate
   exception for targets whose retries were exhausted.

All target failures are retryable. This includes network, authentication,
business-response, and subprocess-start failures because subprocess exit codes
do not currently expose a reliable failure category.

## Compatibility

- Existing `CHECKIN_CRON`, `TZ`, and `CHECKIN_TARGETS` behavior remains valid.
- Retry count, retry interval, and random-delay range are fixed constants for
  this change; no new environment variables are introduced.
- Existing platform modules and Cookie Cloud behavior are unchanged.
- Sites are expected to treat repeat check-in attempts idempotently; current
  platform modules already recognize already-completed states where applicable.

## Operational Considerations

- A run with three targets that all fail adds up to three retry minutes, in
  addition to the initial random delay of up to 30 minutes.
- Container shutdown during a random or retry sleep stops the process normally;
  no retry state is persisted across restarts.
- Logs must identify the target, attempt number, retry interval, and chosen
  random delay without including cookies or V2EX action tokens.
