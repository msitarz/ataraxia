# 25. Retire test-to-criterion markers

Date: 2026-10-15

## Status

Accepted

## Context

The covers marker creates a second mapping to maintain as Work outcomes are
split or rewritten. The migration inventory found that its literal Work paths
refer to retired contracts or synthetic fixtures. Neither a marker nor a static
reference check establishes that assertions prove an outcome.

## Decision

Retire `pytest.mark.covers`, its registration, and ac-collect/ac-test. Select
relevant tests through ordinary Make/pytest routes and assess coverage through
code, tests, execution results, and review. Keep criterion IDs for contract
review without replacing decorators with mapping files or reports.

Explicit markers make criterion-based lookup convenient, but that convenience
does not justify maintaining a parallel index. Without it, reviewers must
consider existing coverage as well as tests changed in the PR. Any retained
ac-check is declaration-only; the tooling Work may remove it if it does not earn
its maintenance cost.

## Consequences

Remove marker infrastructure without deleting useful behavioral regressions.
Focused commands and example-test scope remain available. Current evidence and
test-selection rules live in [Work acceptance](../acceptance-tracing.md) and
[testing guidance](../testing.md). The
[tooling Work](../feat/work-contract-migration/tooling/README.md) owns actual
removal and its tests; this decision does not claim those changes are delivered.
