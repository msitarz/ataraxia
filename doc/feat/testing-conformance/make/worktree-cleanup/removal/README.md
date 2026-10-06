# Worktree removal and refusals

Migrate clean removal with literal hostile paths, branch/unrelated-worktree
retention, and worktree-remove missing input. Extract help listing as an
independent test. Preserve main, dirty, untracked, locked, unknown, and
submodule refusals with exact exit codes, distinctive reasons, and complete
relevant file, ref, and registration snapshots. Retain original covers
provenance. Reuse delivered typed real-Git support narrowly; add only bounded
working-directory support if required for submodule arrangements. No fixture
framework or production changes. Include cleaned modules/helpers in strict
Pyrefly; leave pruning cases and their necessary legacy support for the next
child.

- **AC-1 DONE** Given an eligible clean worktree with a hostile literal path,
  removal deletes only that worktree while retaining its branch and unrelated
  worktree; caller expressions never execute, and help lists cleanup targets.

  Validation: run focused marked removal/help cases and strict typecheck; review
  independently expected effects, original provenance, and latest-head full CI.
- **AC-2 DONE** Given missing input, an unknown worktree, or an unsafe main,
  dirty, untracked, locked, or submodule worktree, refusal preserves required
  files, refs, and registrations and reports the precise reason.

  Validation: run marked refusal cases; compare complete relevant before/after
  snapshots and exact exits, and require latest-head full CI.
