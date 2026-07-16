# Add Check-in Retries and Random Schedule Delay

## Goal

Reduce transient network-related check-in failures and avoid running every
deployment at an exactly predictable time.

## Background

- The scheduler currently runs immediately when `CHECKIN_CRON` fires.
- `run_targets` executes every configured target once, continues after target
  failures, and raises an aggregate error after all targets have been attempted.
- Individual attendance integrations already add a short random delay between
  accounts, but there is no run-level random delay or target retry behavior.

## Requirements

- After each cron trigger, delay the scheduled check-in by a random duration
  between 0 and 30 minutes.
- Apply retry behavior independently to every configured target when its
  subprocess exits unsuccessfully or cannot start.
- Make at most three total attempts per target.
- Wait 30 seconds between failed attempts.
- Preserve bounded failure output, target ordering, and aggregate failure
  reporting after retries are exhausted.
- Log the selected random delay and retry progress without exposing secrets.
- Keep time and randomness injectable so tests do not actually sleep.

## Acceptance Criteria

- [x] A cron occurrence produces one random delay in the inclusive 0–1800
  second range before starting target execution.
- [x] Successful first attempts are not retried.
- [x] A failed attempt can be followed by two retries, for three attempts total.
- [x] There are two 30-second waits when all three attempts fail.
- [x] A later successful retry makes that target successful.
- [x] Exhausted failures retain recent output and participate in aggregate
  failure reporting.
- [x] Automated tests cover the boundaries without real sleeping or randomness.
