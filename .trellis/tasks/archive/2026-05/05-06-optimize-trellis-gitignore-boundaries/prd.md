# Optimize Trellis Gitignore Boundaries

## Goal

Make Git tracking rules match Trellis' local architecture: commit project knowledge, workflow, specs, tasks, platform integrations, and workspace journals; keep local runtime state, developer identity, backups, caches, and temporary files ignored.

## What I Already Know

- `.trellis/workflow.md`, `.trellis/config.yaml`, `.trellis/spec/`, `.trellis/tasks/`, `.trellis/workspace/`, and platform directories are project-local Trellis sources of truth.
- `.trellis/.runtime/` is session-level runtime state and should not be committed.
- `.trellis/.developer` is local developer identity and should not be committed.
- `.trellis/.template-hashes.json` and `.trellis/.version` are management metadata and are currently tracked.
- Root `.gitignore` currently ignores `.trellis/workspace/`, but `.trellis/workspace/toph/index.md` and `journal-1.md` are already tracked. This conflict caused `add_session.py` to fail auto-adding workspace changes.
- `.trellis/.gitignore` already ignores `.runtime/`, `.developer`, `.backup-*`, temp files, task runtime files, and Python caches under `.trellis/`.

## Requirements

- Update ignore rules so `.trellis/workspace/**` is no longer broadly ignored.
- Keep local-only Trellis runtime files ignored:
  - `.trellis/.developer`
  - `.trellis/.runtime/`
  - Trellis backup directories
  - Python caches
  - temporary/conflict/runtime scratch files
- Add comments that document which Trellis paths are intended to be tracked and which are local-only.
- Ensure `git status --ignored` shows no unexpected Trellis workspace journal files as ignored.
- Track `.trellis/workspace/index.md` if it exists and is intended as the global workspace overview.

## Acceptance Criteria

- `git check-ignore -v .trellis/workspace/toph/journal-1.md` returns no ignore match.
- `git check-ignore -v .trellis/.runtime .trellis/.developer .trellis/.backup-*` still reports ignore matches.
- `git status --ignored --short .trellis` clearly separates tracked/trackable Trellis memory from ignored runtime/cache/backup files.
- No secrets or runtime session files are added.

## Out of Scope

- Changing Trellis task workflow behavior.
- Changing platform hooks or agent definitions.
- Rewriting Trellis scripts.
