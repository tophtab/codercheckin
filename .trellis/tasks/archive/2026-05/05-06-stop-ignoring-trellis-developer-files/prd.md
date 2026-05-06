# Stop Ignoring Trellis Developer Files

## Goal

Revise Trellis Git ignore rules so `.trellis/.developer` is trackable, runtime/session-state files remain ignored, and obsolete Trellis backup directories are removed.

## What I Already Know

- Root `.gitignore` explicitly ignores `.trellis/.developer`.
- `.trellis/.gitignore` also ignores `.developer`, `.current-task`, `.runtime/`, `.ralph-state.json`, `.agents/`, `.agent-log`, `.session-id`, `.plan-log`, backup directories, temp files, and Python caches.
- A prior archived task intentionally kept `.trellis/.developer` and runtime files ignored, so this task is revising that policy.
- The user first chose the broad option to stop ignoring Trellis-internal files, then asked for a concrete sensitivity assessment of runtime files before deciding whether they should be pushed.
- Current observed runtime-state contents are low-sensitivity metadata:
  - `.trellis/.developer` contains `name=toph` and an initialization timestamp.
  - `.trellis/.runtime/sessions/*.json` contains platform name, last-seen timestamp, current task path, and current run status.
- Current observed backup directories are `.trellis/.backup-2026-04-29T03-09-32` and `.trellis/.backup-2026-05-06T01-19-56`; they are full Trellis/config snapshots rather than active working files.

## Assumptions (Temporary)

- `.trellis/.developer` should become trackable.
- Runtime/session files are not highly sensitive in the current repo state, but should stay ignored because they are machine/session-scoped and noisy.
- Backup snapshot directories are safe to delete because the user does not want rollback copies.

## Open Questions

- None.

## Requirements (Evolving)

- Remove ignore rules that conflict with the confirmed tracking policy for `.trellis/.developer`.
- Keep runtime/session-state files ignored in `.trellis/.gitignore`, including `.runtime/`, `.current-task`, `.ralph-state.json`, `.agents/`, `.agent-log`, `.session-id`, `.plan-log`, temp files, and Python caches.
- Delete existing `.trellis/.backup-*` directories.
- Keep ignore behavior aligned between root `.gitignore` and `.trellis/.gitignore`.
- Update comments so the intended tracking policy is explicit, including that `.developer` is intentionally trackable while runtime/session artifacts are not.

## Acceptance Criteria (Evolving)

- [ ] `git check-ignore -v .trellis/.developer` returns no ignore match.
- [ ] `git check-ignore -v .trellis/.runtime/sessions/<session>.json` still reports an ignore match.
- [ ] Existing `.trellis/.backup-*` directories are removed.
- [ ] Comments in ignore files match the final Trellis tracking policy.
- [ ] No contradictory Trellis ignore rules remain after the change.

## Definition of Done (Team Quality Bar)

- Tests added/updated where appropriate
- Lint / typecheck / CI green when applicable
- Docs/notes updated if behavior changes
- Rollout/rollback considered if risky

## Out of Scope (Explicit)

- Changing Trellis workflow behavior
- Changing Trellis scripts or agent definitions

## Technical Notes

- Relevant files inspected: `.gitignore`, `.trellis/.gitignore`
- Prior related task: `.trellis/tasks/archive/2026-05/05-06-optimize-trellis-gitignore-boundaries/prd.md`
