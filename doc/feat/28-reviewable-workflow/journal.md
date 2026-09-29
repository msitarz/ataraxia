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

## J-6: Review diffs in the maintainer's tools

Date: 2026-09-29. Role/session: defining session, this conversation.

The maintainer clarified item 2: the agent must not print the diff. Assume review
in Magit or an editor/IDE, followed by discussion with the agent. Revised the
contract to identify the revision/comparison range and affected files, keep the
chat entry point concise, and explain changes in response to review questions.

Correction plan: revise the contract and append this event; check and commit the
change; update the candidate revision in the overview, check and commit that
handoff, and publish to the existing draft PR. This instruction authorizes the
specification correction, not implementation of the proposed workflow.

Validation: the bounded metadata/ID/link checks and whitespace check passed;
`make ci` passed with 232 repository tests, 3 examples, type/import checks,
installed-wheel smoke and audit. No executable behavior changed.

## J-7: Acceptance namespaces and planned checks

Date: 2026-09-29. Role/session: defining session, this conversation.

The maintainer asked whether parent and child acceptance IDs were file-scoped
and whether the intended `make docs-check` should enforce their scope. Made the
owning feat/slice namespace contract explicit, including frontmatter resolution,
qualified external references, uniqueness, file moves, and retired IDs. Added
static namespace/reference checks to slice 03 and shared-index pytest checks to
slice 04. These are requirements for future tooling, not an implemented target.

Correction plan: update the owning contract and checker slices, verify and
commit; advance the candidate revision in the overview, verify that handoff,
commit and publish through the existing draft PR. Review remains pending.

Validation: bounded package checks passed for 38 scoped acceptance rows and
71 local links/anchors, including namespace ownership and uniqueness. `make ci`
passed with 232 repository tests, 3 examples, type/import checks, wheel smoke
and audit. Only proposal documents changed; no checker was implemented.

## J-8: Journal identity and session registration

Date: 2026-09-29
Role: defining
Session: S1

Session declaration, scoped to journal owner `F28`:

```yaml
session_ref: S1
name: Reviewable workflow definition
provider: codex
thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

Legacy association: `F28:J-1`, `F28:J-2`, `F28:J-3`, `F28:J-4`, `F28:J-5`,
`F28:J-6`, and `F28:J-7` identify this same defining conversation as
"this conversation". They refer to `F28:S1`. Verified its native thread ID from
`CODEX_THREAD_ID` and the matching local session metadata record; no transcript
content is copied into the repository. This append preserves the earlier entries.

The maintainer agreed to native provider/thread identity, separate delivery role,
and planned structural checks with optional local history availability. Made
journal-event scope and session-reference contracts explicit and added their
schema/reference/history fixtures to slice 03. The handoff links to this declared
session. These records do not establish independent review or approve the full
specification.

Correction plan: revise the owning contract, design and checker slice; append
this declaration and update the handoff; verify, commit, advance the candidate
revision in a checked metadata commit, and publish through the existing draft PR.
No workflow tooling or parallel implementation changes are part of this step.

Validation: bounded checks passed for all 10 proposal documents, 39 scoped
acceptance rows and 74 local links/anchors. Checked the declared native identity,
legacy association and handoff, and confirmed all earlier journal text remains
unchanged. `make ci` passed with 232 repository tests, 3 examples, type/import
checks, installed-wheel smoke and audit. Proposed journal checks remain unbuilt.

## J-9: Visual review prototype

Date: 2026-09-29
Role: defining
Session: S1

The maintainer requested Mermaid diagrams in the specification and design for
viewing on GitHub. Added two small views to each: the iteration approval loop
and acceptance namespaces, then document ownership and proposed checker
composition. Captions route to the owning contracts and distinguish proposed
tools from adopted gates. The prototype tests navigation and visual review;
it does not establish reduced fatigue or make diagrams a second specification.

Plan: add the visual companions and this event; check links, Mermaid rendering,
contract consistency and repository CI; commit; update the candidate revision
in a checked metadata commit; publish to the existing draft PR. The maintainer
can then assess whether these views make review easier.

Validation: `make ci` passed with 232 repository tests, 3 examples, type/import
checks, installed-wheel smoke and audit. Bounded checks passed for 39 scoped
acceptance rows and 82 local links/anchors. Rendering was not verified; the
maintainer requested publishing directly and will inspect the diagrams on GitHub.

## J-10: Accept the visual review format

Date: 2026-09-29
Role: defining
Session: S1

The maintainer reviewed the published prototype and said, "yeah i really like it.
We will adopt it." This accepts the visual companion format and the four views
in `spec.md` and `design.md` at revision
`47c2e57e9c63e550a57c014bb1db89a2c576abbe`. The approval covers this format;
it does not approve execution of the entire workflow specification.

Added the visual companion rule to the owning record contract and planned
templates in slice 01; removed the prototype qualifier from the visual headings.
Precise requirements remain in prose, and diagrams illustrate one review question
at a time. The maintainer's feedback is the prototype result; no independent
browser verification or measured fatigue reduction is claimed.

Plan: record this scoped approval and template contract, check and commit the
proposal amendment, then advance its candidate revision and publish through the
existing draft PR. Browser configuration guidance remains outside repository
workflow policy, and no browser setup or rendering attempt is part of this step.

Validation: bounded checks passed for 39 scoped acceptance rows and 84 local
links/anchors. `make ci` passed with 232 repository tests, 3 examples, type/import
checks, installed-wheel smoke and audit. Earlier journal entries remain intact.

## J-11: Note calldiff for future review

Date: 2026-09-29
Role: defining
Session: S1

The maintainer reaffirmed Mermaid for the workflow and suggested calldiff as a
future code-review aid. Read its README and agent skill, then added an optional
candidate note to slice 02 with a bounded probe for usefulness and missed edges.
No installation, runtime evaluation, new gate or mandatory delivery step is
authorized by this note.

Plan: record the candidate and this event, check and commit the documentation,
advance the candidate revision, then publish through the existing draft PR.

Validation: bounded document and whitespace checks passed. `make ci` passed
with 232 repository tests, 3 examples, type/import checks, installed-wheel smoke
and audit. No calldiff runtime claims were tested.
