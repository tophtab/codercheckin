# Show V2EX Check-In Copper Reward

## Goal

When a V2EX daily check-in succeeds, the runtime log and Telegram success message should show how many copper coins were awarded for that check-in. This makes the Docker/NAS logs more informative without changing the check-in flow.

## What I Already Know

- The user asked whether V2EX check-in logs can show how many copper coins were obtained.
- V2EX check-in logic lives in `v2ex/v2ex.py`.
- The module already fetches `/balance` after redeeming the daily mission and parses rows containing `每日登录奖励`.
- `_parse_balance_daily_rewards()` currently returns `(reward_time, reward_value)`, where `reward_value` is the balance after the reward, not the delta.
- A real balance row can include right-aligned numeric cells such as `9.0` and `13881.28`, plus a description cell like `20260511 的每日登录奖励 9 铜币`; the description is the most reliable source for the integer copper reward amount.
- Existing tests live in `tests/test_v2ex.py` and cover balance parsing, success confirmation, secret redaction, and successful main flow behavior.

## Assumptions

- "获得多少铜币" means the per-check-in reward amount shown in the balance row, for example `9`, not the resulting account balance.
- If V2EX changes the balance page shape and the reward delta cannot be parsed, check-in should still succeed when today's reward can be confirmed, and the log/message should omit the reward amount or use the existing generic success text.
- No cookies, redeem `once` tokens, or full headers should be logged.

## Requirements

- Parse the daily reward delta from V2EX balance rows.
- Use today's `每日登录奖励` balance entry after redeem to confirm success and obtain the reward delta.
- On successful redeem, include the reward amount in runtime logs.
- On successful redeem, include the reward amount in the success message sent to Telegram.
- Preserve idempotent "already signed today" behavior.
- Preserve existing failure behavior when the balance page does not confirm today's reward.
- Preserve import safety and finite request timeouts.

## Acceptance Criteria

- [ ] A successful V2EX redeem whose balance page contains today's daily reward row with `+N` records/logs the reward amount.
- [ ] The Telegram message includes a clear success line with the reward amount when it is parsed.
- [ ] Existing success confirmation still works when only today's balance entry is needed.
- [ ] Failure paths do not expose the redeem action token.
- [ ] Tests cover parsing the reward delta and the successful message/log behavior.

## Definition of Done

- Tests added or updated for affected V2EX behavior.
- `python3 -m py_compile v2ex/v2ex.py` passes.
- Targeted V2EX tests pass.
- Logging remains timestamped through `runtime_log.log(...)`.

## Out of Scope

- Changing the V2EX request/header strategy.
- Fetching or displaying total account balance outside the existing balance confirmation page.
- Supporting multiple V2EX accounts.
- Changing other platform check-in logs.

## Technical Notes

- Relevant specs:
  - `.trellis/spec/backend/index.md`
  - `.trellis/spec/backend/logging-guidelines.md`
  - `.trellis/spec/backend/quality-guidelines.md`
- Relevant implementation area discovered by inspection:
  - `v2ex/v2ex.py`
  - `tests/test_v2ex.py`
- Real-page reference:
  - `/balance` daily reward rows can render the reward as `9.0` in the amount cell and `每日登录奖励 9 铜币` in a later description cell.
