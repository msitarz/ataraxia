# Testing conformance

Bring the Make, script, and Ataraxia suites into conformance with
[testing guidance](../../testing.md), then introduce bounded Hypothesis pilots.
Preserve observable behavior and Work coverage while replacing weak or bypassed
assertions, checkout mutations, and duplicated process plumbing.

## Delivery map

- **TODO** [Make boundaries](make/README.md): fast orchestration tests and a
  small retained set of real-tool regressions.
- **TODO** [Script boundaries](scripts/README.md): correct test types, explicit
  process environments, and independently expected validation results.
- **TODO** [Ataraxia boundaries](ataraxia/README.md): real product execution,
  complete outcomes, and explicit lifecycle and trading boundaries.
- **TODO** [Hypothesis pilots](hypothesis/README.md): adoption followed by
  independent window, Work-path, and Make-argument properties.

Merge this map before child planning PRs. Each subtree next defines its leaf
contracts in separately reviewable planning deliveries; these summaries are
planned outcomes, not active leaf contracts. Deliver Make first. Reassess each
complete diff against the
[five-minute review target](../../workflow.md#scope-and-sizing) before dispatch
and publication; split and merge revised maps before expansion. Sequence
children sharing helpers, configuration, tests, or parent maps.

Product APIs, coverage-threshold reductions, wholesale property-test conversion,
and Git or broker state machines are outside scope. Discovered production
defects become separately bounded repair Works. Follow
[test ownership](../../test-ownership.md) before removing probes and preserve
their historical execution evidence.

## Acceptance

- **AC-1 TODO** Given the completed cleanup, changed tests exercise their named
  public boundaries with independent expectations and preserve existing
  contracts and Work coverage; tests create files only in disposable
  arrangements.

  Validation: independently review child diffs and their focused
  execution evidence against common and relevant test-type guidance.
- **AC-2 TODO** Given Make orchestration targets, real Make with fake uv proves
  command arguments, environment, ordering obligations, and failure propagation;
  real Git and selected real tools retain distinct repository-boundary coverage.

  Validation: review the Make subtree's criterion-marked execution evidence and
  retained regressions; confirm normal test and CI selection includes all cases.
- **AC-3 TODO** Given prepared offline runs, Make timing evidence compares three
  baseline and three final runs under matched conditions, reporting full-suite
  and unmarked-case medians, failures, and skips without an assumed speedup.

  Validation: review the declared measurement protocol and retained
  observations; timing alone cannot justify loss of contract coverage.
- **AC-4 TODO** Given fresh per-example arrangements, separate Hypothesis pilots
  prove window ordering, Work-path containment, and literal Make argument
  transport while preserving named examples.

  Validation: review each pilot's independent oracle, generated execution
  evidence, state isolation, and bounded configuration.
