# Worktree creation cases

After helper delivery, migrate the six existing creation cases: success,
missing/partial cache, verification failure, and destination/branch conflicts.
Use the typed helper with real Git and cache copying; preserve original covers
provenance. Assert complete relevant before/after files, refs, and worktree
registrations, destination-local routing, literal hostile names, and absent
execution markers. Use exact exit codes and Given/When/Then, with complete
parametrized arrangements instead of test-body branching. Include cleaned files
in strict Pyrefly; remove the obsolete legacy module only when empty.
No helper expansion, production changes, or other test responsibilities.

- **AC-1 TODO** Given usable, missing, partial, or verification-failing setup,
  creation succeeds with independent destination caches/environment or fails
  with the recoverable worktree retained; hostile input never executes commands.

  Validation: run marked success/setup-failure cases and strict typecheck;
  review precise failures, routing, retained state, original provenance, and
  full CI.
- **AC-2 TODO** Given an existing destination or branch, refusal preserves
  existing files/refs/registrations and creates no unintended worktree.

  Validation: run marked conflict cases; independently compare before/after
  state, verify legacy removal preserves coverage, and require full CI.
