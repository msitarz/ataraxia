---
id: F28-JOURNAL
kind: journal
owner: F28
---

# Workflow definition and execution journal

Append consequential events. Corrections refer to an earlier event; Git owns
complete textual history. Current state and next action belong in the overview.
These records are evidence claims, not independent review or approval.

## J-1: Direction and branch base

Date: 2026-09-29. Role/session: defining session, this conversation.

The maintainer requested compilation of the brainstorming into the next workflow
feat using the proposed directory layout and the six review principles. They
explicitly requested branching from the current branch so a later parallel replay
can evaluate the adopted workflow. This authorizes proposal preparation and its
publication; it does not approve the proposed specification or a code reversal.

Inspected clean base: `feat/parallel_execution` at
`220e3f1f94ca910baee07984c10b483b4499dc6e`. Created
`feat/reviewable-workflow` and [issue #28](https://github.com/msitarz/ataraxia/issues/28).
The issue tracks implemented capability, so proposal publication uses `Refs #28`.

## J-2: Compilation choices

Date: 2026-09-29. Role/session: defining session, this conversation.

Selected `README.md` as the directory entry point, kept one initial journal,
and split adoption into six outcome slices. Separated observable contracts from
the proposed checker design and mutable handoff. Retained plain pytest rather
than behave/Gherkin, YAML metadata, explicit structural review, bounded prototype
and migration guidance, and optional Markdown-vault viewing. Unslop is excluded
at the maintainer's request. These are proposed choices, not implemented gates.

The drafting plan is: create branch/issue; compile the package and planned shared
terms; inspect ownership, references, and scope, run required checks, and commit;
publish a draft PR and append validation/publication evidence in a checked commit.
Detailed implementation steps live in the individual delivery slices.

## J-3: Initial source inspection

Date: 2026-09-29. Role/session: defining session, this conversation.

Read current workflow, documentation ownership, engineering and contribution
guidance, glossary, architecture, relevant ADRs, parallel slice, Makefile, and
tool configuration. Existing CI has code/type/import/behavior/package checks,
but no `docs-check` target or acceptance coverage marker. Parallel implementation
and both P2 corrections are present; its manual and defining-session reviews
remain pending.

Read primary rumdl documentation and the sourdough checker repository. Confirmed
open upstream reports for its documented package install and uv model setup;
links and proposed reproductions are in slice 02. No checker installation, model
download, execution probe, or local reproduction was performed for this proposal.
Tool suitability and full STE conformance have not been established.

The two parallel P2 corrections address receipt/deadline correctness and full
exception-group diagnostics already required by its approved contracts. The
replay must retain those contracts and regressions; it must not describe every
review correction as a specification gap.

## J-4: Proposal validation

Date: 2026-09-29. Role/session: defining session, this conversation.

Inspected the package for contract/design/state ownership, planned versus current
behavior, preserved historical scope, and reviewable navigation. Added only two
explicitly planned shared terms to the glossary and reread it. No application
code, adopted workflow rules, tool dependencies, or parallel implementation
changed; no structural code refactoring was needed.

A temporary check using the prepared environment's Markdown parser and YAML
loader passed for all 10 package documents: headers and scoped IDs, 37 acceptance
rows, and 68 relative links/anchors across the package and changed glossary.
This was a bounded check of this proposal, not the proposed semantic checker.

`make ci` passed on Python 3.14.7: 232 repository tests, 3 example tests,
91.56% branch-inclusive coverage, Ruff checks/formatting, strict Pyrefly and all
11 expected negative diagnostics, Tach, tracked-file checks, installed-wheel
smoke in both execution modes, and an audit of 38 packages without known
vulnerabilities. `git diff --cached --check` passed. The first attempt identified
a fenced Python example formatting issue, which was corrected before the clean
run. Evidence is local macOS validation, not a new workflow evaluation or STE run.

## J-5: Proposal publication

Date: 2026-09-29. Role/session: defining session, this conversation.

Committed the proposal as `999858b67ee44bb328954057375435f04f284541` and pushed
`feat/reviewable-workflow`. Created [draft PR #29](https://github.com/msitarz/ataraxia/pull/29)
against `feat/parallel_execution`, with `Refs #28`. Added tracking links to the
overview and issue. The specification/design/slice bodies remain at that candidate
revision; this publication update changes navigation and historical evidence.

No specification approval, executor session, independent defining-session review,
STE runtime result, workflow adoption, or reversal has been recorded. The next
decision is the maintainer's specification review, routed by the overview.
