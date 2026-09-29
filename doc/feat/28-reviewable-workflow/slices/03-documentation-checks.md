---
id: F28-03
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Add documentation checks with honest selection

## Outcome and scope

Deliver the [checker composition and command contract](../design.md#checker-composition)
chosen after slice 02. Add `make docs-check` to `verify-check` so local and CI
evidence use the same non-mutating gates. Keep generic checks in adopted tools
and repository-specific rules in a small typed Python checker.

Choose explicit document-kind schemas. Check IDs, status/stage separation,
required fields/headings, references and ownership routes, ADR number/status
and reciprocal amendment/supersession links. Require frontmatter for newly
enrolled kinds. Preserve historical records through explicit compatibility
profiles; do not require unexplained ADR numbering continuity.

History checks compare covered approved contracts and append-only journals at
declared revisions. Changes to accepted ADR bodies and completed historical
slices follow their existing amendment policy. Approval-record consistency is
checkable; human authority and understanding remain review responsibilities.

## Proposed iterations

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | Pinned generic linter config and a small enrolled doc set; review diagnostics and exclusions | Chosen rumdl rules and fixture probes; `make verify-check` |
| 2 | A first schema/state rule and shared parsing/index seam; review one failing and one clean document | Parser/schema unit fixtures, precise locations, invalid metadata and tool-failure exit codes |
| 3 | Navigation/reference and ADR reciprocity rules, introduced one coherent rule per review | Dangling links/IDs, unreachable required routes, contradictory reciprocal records; reuse generic link checks where adequate |
| 4 | Path/directory, staged-index and base-ref selection; review affected-file explanations | Integration fixtures for inbound links, code-only changes, deleted/renamed files, changed config, and an unstaged fix hiding a staged failure |
| 5 | Approval/revision and append-only transition checks; review their limits | Git-history fixtures including a newly created branch-local spec, contract changes after approval, journal correction append and unauthorized body rewrite |
| 6 | Make/CI/hook integration and documentation; review a real failing-to-clean run | Full `make docs-check`, targeted examples, missing required capabilities, history base configuration and `make ci` |

Every row can split into smaller iterations. Extend strict type checking to the
checker code and test meaningful malformed inputs rather than mirror its parser.
Use current integration tests for Makefile behavior where applicable. Defer
caching, automatic fixes, plugin APIs, similarity heuristics, and broad doc/code
drift inference until evidence requires them.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Run full checks on clean and malformed enrolled fixtures | Correct kinds, schema, structure and graph rules produce actionable locations; tools leave files unchanged | Unit/integration tests and `make docs-check` |
| AC-2 | Select a path, staged changes or changes since a base | Required related files and global constraints remain checked; staged mode evaluates index contents | Selection and Git-index integration tests |
| AC-3 | Change approved contracts, accepted records or journal history | Applicable transition violations are reported, including new branch-local approved specs; proper amendments/correction appends pass | Git-history fixture tests |
| AC-4 | Remove a required tool/model/base, or run offline | Required checks fail or report incomplete; optional/unavailable transition checks are named and never claimed performed | CLI/integration tests |
| AC-5 | Invoke repository verification and CI | Documentation gates run through the shared target with clear exit codes and compatible hook behavior | Makefile integration tests and `make ci` |

## Next review

The [journal](../journal.md) records enrollment, revisions, findings and approvals.
Acceptance-test mapping belongs to slice 04; language integration belongs to
slice 05. Metadata or a successful checker cannot replace manual review.
