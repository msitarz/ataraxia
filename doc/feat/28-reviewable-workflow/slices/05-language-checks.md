---
id: F28-05
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Pilot language checks without weakening contracts

## Outcome and scope

Use the STE investigation in slice 02 to choose a documented rule subset and
representative pilot, or record a reviewed deferral when no suitable checker
exists. The goal is precise, readable instructions and contracts, with mechanical
help where it is reliable. Passing an unofficial checker is not certification
of ASD-STE100 conformance.

Prefer deterministic local CLI checks; MCP/editor integration is optional later.
Treat descriptive prose and procedures separately. Decide profiles for workflow
instructions and contracts first; evaluate ADR tradeoffs and journal fragments
before enrolling them. Avoid a repository-wide prose rewrite during adoption.

## Proposed iterations

| Step | Concrete artifact and decision | Verification and proposed checkers |
| --- | --- | --- |
| 1 | A selected-engine decision, supported-rule profile and short corpus report; review whether to adopt or defer | Slice 02 reproducibility/quality findings, glossary and modal-strength examples, maintainer decision |
| 2 | If needed, a small Markdown adapter with original source locations; review what prose reaches the engine | Tests excluding frontmatter/code/URLs and handling table prose, lists, mixed procedure/description blocks and technical terms |
| 3 | A reproducible locked setup and offline invocation; review installation and ongoing costs | Fresh uv environment, explicit interpreter/model installation, model/version pinning, doctor/check outcomes and missing-model failure |
| 4 | One enrolled instruction document and one contract excerpt; review meaning and readability | Selected STE checks plus rumdl/schema checks, before/after semantic review and justified narrow exceptions |
| 5 | Shared `docs-check` integration or a recorded deferral; review the result and any remaining limits | Machine output/exit tests, required-check failure, full checks and `make ci` if integrated |

Check one cohort at a time. Technical glossary entries must reflect approved
meanings, not suppress inconvenient findings. Allow scoped exceptions with
reasons. If rule exclusion, Markdown extraction, or packaging requires a large
fork, return with its maintenance cost before implementing it.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Review candidate findings and the proposed pilot | Adopt/adapt/defer decision names capabilities, false positives, supported rules and costs | Manual decision with linked investigation evidence |
| AC-2 | Feed representative Markdown and technical vocabulary, if adopted | Only intended prose is analyzed with usable original locations and explicit profiles; code/metadata stay intact | Adapter/corpus tests and sample diagnostics |
| AC-3 | Run from a fresh supported environment, if adopted | Pinned setup succeeds reproducibly; checks run offline; required tool/model failures cannot silently skip | Setup and CLI integration evidence |
| AC-4 | Review rewritten pilot text or a deferral | Contracts retain behavior and modal strength; adopted checks integrate, or limitations and revisit conditions are recorded | Manual semantic review plus `make docs-check` and `make ci` if adopted |

## Next review

An accepted deferral completes the suitability decision, not a language-gate
implementation. Record that distinction in the [journal](../journal.md) and
overall acceptance evidence. The parallel evaluation can then proceed with the
actually adopted gates and an explicit limitation.
