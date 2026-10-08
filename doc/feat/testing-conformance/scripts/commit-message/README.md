# Commit-message testing boundaries

Clean the current `test/script/integration/test_commit_message.py` boundaries
without changing checker or hook behavior. Follow
[parent obligations](../README.md).

## Delivery map

- **TODO** [Typed arrangements](support/README.md): isolated process/Git support
  and a named executable hook fixture, before any consumer migration.
- **TODO** [Checker CLI](checker/README.md): all 18 accepted and seven refused
  formatting cases, with independent complete outcomes and retained bytes.
- **TODO** [Configured Git behavior](git/README.md): six scissors combinations
  and the real commit-hook refusal/acceptance lifecycle.
- **TODO** [Prepared-project prek](prek/README.md): separate filename-forwarding
  success/refusal tests using real prepared tools in a disposable project.

Merge this map before implementation; deliver leaves in listed order. Each leaf
owns only its listed modules/subsets and strict includes, and updates this map
serially. Remove migrated cases from the legacy module without rewriting its
remaining cases; the last leaf removes the empty legacy module. Existing
script-wide helpers/conftest and Make consumers need no migration. Reassess each
complete diff against the five-minute target and split before expanding it.

Preserve accepted/absent messages, long subjects/tokens/trailers, body separator
and width refusals, CRLF, comments and verbose diff handling. Use exact exits,
distinctive reasons and unchanged message bytes. Real Git refusal must leave
refs unchanged; accepted commit content is independent expected text. Split
prek success/refusal cases instead of loops in a test body.

Use explicit disposable HOME/TMPDIR, isolated Git configuration and captured
timeout-owning processes. Actual checker/Make/Git/prek boundaries stay real;
prek comes from the prepared project, without global Homebrew dependency or
network installs. Named hook source stays in fixtures. Repairing generated hook
launchers or tool-location policy is a separate Work, not part of this cleanup.
Retain regression tests for our boundary; assess upstream-only probes under
[test ownership](../../../../test-ownership.md) before any removal.

All cleaned tests/helpers/executable fixtures receive precise annotations and
explicit normal strict-Pyrefly inclusion; broad types, casts, ignores, and
unchecked fixture dependencies cannot stand in for that adoption. Preserve case
identities and existing coverage provenance. This session authorizes concise
slice docstrings describing actual coverage instead of copying criterion text.

- **AC-1 TODO** Given disposable messages/repositories and prepared project
  tools, checker, configured Git hook and prek preserve formatting contracts,
  exact failure effects and accepted content without changing caller state.

  Validation: review process isolation, literal outcomes and retained boundary
  coverage; run each leaf's focused cases and complete commit-message module,
  strict typing, lint/format, doc/ac checks and latest-head full CI.
