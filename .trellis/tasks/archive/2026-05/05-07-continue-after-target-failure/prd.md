# Continue Remaining Check-In Targets After Target Failure

## Goal

When one configured check-in target fails, the runner should continue executing the remaining targets and report all failures after the full target list has been attempted. A transient or site-specific failure, such as a DeepFlood security challenge, should not prevent V2EX or any later target from running.

## What I Already Know

* `run_targets()` currently executes targets sequentially and raises `TargetExecutionError` immediately when one target fails.
* The default target order is `nodeseek,deepflood,v2ex`.
* The observed run succeeded for `nodeseek`, failed for `deepflood`, marked the whole scheduled run failed, restarted the process, and never started `v2ex`.
* Existing tests in `tests/test_checkin_runner.py` assert the current fail-fast behavior and must be updated.
* `scheduler.py` already treats `TargetExecutionError` as a whole-run failure, so the runner can still raise after attempting every target.

## Requirements

* `run_targets(targets)` must attempt every target in the input order, even if one or more earlier targets fail.
* A successful target must continue to log its existing success message.
* A failed target must continue to log the existing failure summary and recent output block.
* Subprocess start failures must be handled like other target failures: log the failure, keep going, and include the failure in the final result.
* After all targets have been attempted:
  * return `0` if every target succeeded;
  * raise an error if any target failed.
* The final raised error must preserve useful target context for callers and logs, including the failed target name, return code when available, and recent output.
* If multiple targets fail, the final error message should make that clear and summarize each failed target rather than hiding all but the first failure.

## Acceptance Criteria

* [ ] Given targets `["nodeseek", "deepflood", "v2ex"]` where DeepFlood exits non-zero, `v2ex` is still started.
* [ ] Given one failed target and later successful targets, `run_targets()` raises only after the later targets finish.
* [ ] Given multiple failed targets, the raised error message includes each failed target's summary.
* [ ] Given a target that fails before subprocess start, later targets are still attempted and the final raised error includes the start failure details.
* [ ] Existing recent-output truncation behavior remains bounded by `RECENT_OUTPUT_LINE_LIMIT`.
* [ ] Scheduler behavior remains compatible: a run with any target failure is still logged as failed after `run_targets()` raises.
* [ ] Relevant unit tests pass.

## Out of Scope

* Changing the target module implementations for NodeSeek, DeepFlood, or V2EX.
* Adding retry logic, target concurrency, or per-target backoff.
* Changing startup cookie validation behavior.
* Changing scheduler restart policy outside the runner's failure semantics.

## Technical Notes

* Primary implementation area: `checkin_runner.py`.
* Primary tests: `tests/test_checkin_runner.py`; scheduler tests may need adjustment only if error type or message semantics change.
* Prefer preserving the existing `TargetExecutionError` API where practical because `scheduler.py` and tests import it directly.
* A small aggregate error type may be appropriate if preserving `TargetExecutionError.target` for a single failure would be misleading for multi-failure runs.
