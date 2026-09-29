---
id: F28-04
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Map acceptance criteria to observed evidence

## Outcome and scope

Keep acceptance tables human readable and plain pytest tests directly reviewable.
Implement the [scoped-ID and marker contract](../design.md#acceptance-evidence),
targeted criterion selection, and mechanical detection of missing or dangling
references. Support explicit evidence from type checks, installed-wheel checks,
other commands, and manual observations. Do not add Gherkin or a second runner.

Proposed slices need valid IDs and evidence plans but no implementation tests.
Validated delivered scope needs current relevant observed evidence. Maintain
separate outcomes for reference coverage and passing execution; neither proves
that the assertions fully establish a requirement.

## Proposed iterations

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | Stable ID rules and one example acceptance table with a retired ID; review readability and evidence ownership | YAML/ID checker fixtures, duplicate/dangling/retired references; rumdl table checks |
| 2 | Registered `covers` marker and collected mapping for a tiny test set; review test-to-criterion links | Pytest collection tests for inherited, parametrized and multiple-AC markers; strict markers remain enabled |
| 3 | Targeted selection, proposed as `pytest --covers F28-04:AC-1`; review selected and deselected item reports | Tests for valid/unknown scope and criteria, malformed arguments, no-match failure, and ordinary unfiltered collection |
| 4 | Observed run and non-pytest evidence reporting; review one validated and one incomplete criterion | Tests for pass, fail, skipped, xfail, partial runs, evidence revision/context, and concrete manual/command records |
| 5 | Enrollment/migration policy and one real new-slice example; review limits before broader retrofit | Full docs/trace checks, existing pytest suite and `make ci`; legacy records retain explicit historical treatment |

Use collection-aware integration rather than treat an AST scan as authoritative.
Keep custom pytest hooks small and independently typed/tested. Report precisely
which criteria a selected run supplies evidence for; it cannot validate the
entire slice by implication.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Add duplicate, retired or unknown acceptance references | Checker rejects invalid references; valid scoped IDs remain stable across edits | Docs-check fixtures |
| AC-2 | Collect inherited, parametrized and multi-criterion tests | Mapping includes actual collected items and rejects dangling criteria under strict markers | Pytest integration tests |
| AC-3 | Select one scoped criterion or an unknown/no-match criterion | Intended tests run; invalid/no-match requests fail clearly; no option preserves normal pytest behavior | Selection integration tests |
| AC-4 | Validate a slice with passing, skipped or stale evidence | Only relevant passing observations count; missing/stale evidence and bare manual claims remain incomplete | Result/evidence integration tests |
| AC-5 | Introduce traceability while historical slices exist | New enrolled scope is enforced without rewriting old approved contracts or claiming old tests satisfy new evidence rules | Migration fixtures and reviewed example |

## Next review

The [journal](../journal.md) owns choices and delivered evidence. Map the parallel
acceptance rows during the separately reviewed evaluation preparation in slice
06, preserving their intended behavior and original record.
