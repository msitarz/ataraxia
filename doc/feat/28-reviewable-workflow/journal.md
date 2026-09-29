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

## J-12: Adopt embedded journal metadata

```yaml
id: J-12
date: "2026-09-29"
kind: decision
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

The maintainer said, "yeah, lets adopt that new format", accepting six entry
kinds and native identity embedded in each entry. The
[entry contract](spec.md#journal-entries-and-session-identity) now specifies the
first YAML block, required fields, review/approval metadata, and ordinary prose
links. The design, template slice and checker slice follow that contract.
This adopts the record format for proposal entries; it does not approve execution
of the complete workflow specification or implement `make docs-check`.

Legacy boundary: [J-1](#j-1-direction-and-branch-base) through
[J-11](#j-11-note-calldiff-for-future-review), inclusive, retain their earlier
prose metadata and S1 convention. Their defining conversation is the native
identity embedded above, previously verified and associated in
[J-8](#j-8-journal-identity-and-session-registration). J-12 begins the new format;
later entries cannot use this historical compatibility boundary. Corrections
append and link to their earlier records; no session registration or YAML
reference list is required.

Plan: revise the owning contract and affected proposal routes, append this
decision, check metadata/links/history and repository CI, and commit. Then
advance the overview's candidate revision in a checked metadata commit and
publish through the existing draft PR. Preserve every earlier journal entry.

Validation: bounded checks passed for all 10 proposal documents, 39 scoped
acceptance rows and 89 local links/anchors. Checked J-12's YAML placement and
fields, verified its native identity, and preserved all earlier journal text.
`make ci` passed with 232 repository tests, 3 examples, type/import checks,
installed-wheel smoke and audit. The future documentation checker remains
unimplemented; these bounded checks do not claim its delivery.

## J-15: Relocate delivery to child PRs

```yaml
id: J-15
date: "2026-09-29"
kind: decision
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

The maintainer accepted separate issues, branches and PRs for each slice and
delivery step, and instructed reversal of all slice 01 commits from the feat,
an amendment of the relevant proposal files, and replay through a slice PR to
the feat. The adopted hierarchy is step PR to slice, slice PR to feat, and feat
PR to its declared integration base. Maintainer approval and merge precede
dependent continuation. The current feat base remains `feat/parallel_execution`.

Authorized source commits, retained in Git history:

- Approval/handoff: `446f86e035738da057b80e13dfbcfb886db85440`.
- Template/example: `efe5d17d06c5b1cd02bba593319ba92eb2b0449e`.
- Review metadata: `f5f4e9e7a58d04f94b8e2384d405f716837d74f1`.

Applied their inverse changes in reverse order at
`a436d07973ad2236b139e2bae6d508d8d618384d`. Verified all four affected files
exactly matched pre-iteration revision `6d1a864bad92ac439bbd1f70fe98ba1699e15abe`.
This explicit migration also reverted J-13/J-14 additions; their IDs remain
reserved. Replay appends their unchanged records to the receiving branches
after this event, preserving identity without renumbering. The earlier J-1
through J-12 text remains intact. The maintainer's instruction authorizes this
specific history transition, not general rewriting of journal records.

Remaining plan:

1. Amend the tracking/review contract, design, relevant slices and handoff;
   check schemas, links, event/criterion IDs, Git state and `make ci`, then commit
   and publish the planning revision on the feat branch.
2. Create a slice integration branch and issue. Replay the approval/handoff
   there, adapting mutable state to the new hierarchy, and publish its draft PR
   to the feat. Record the migration scope at the amended revision.
3. Create a first-step issue/branch from that slice, replay the original
   template/example commit, and publish its draft PR to the slice after checks.
   Keep the slice PR draft until its steps and integration evidence complete.
4. Publish tracking links and exact review revisions, verify actual PR bases,
   and stop for maintainer review. Iteration 2 remains unstarted; agents merge
   nothing. The same conversation performs defining and executor roles.

Validation: reversal equality, whitespace and bounded checks passed for all
10 proposal documents, 42 scoped acceptance rows and 112 local links/anchors.
Checked preserved J-1 through J-12 text, reserved replay IDs and metadata.
`make ci` passed with 232 repository tests, 3 examples, type/import checks,
installed-wheel smoke and audit. The proposed checker remains unimplemented;
the updated Mermaid views await maintainer visual review.

## J-13: Approve slice 01 iteration 1

```yaml
id: J-13
date: "2026-09-29"
kind: approval
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
revision: "406d2e61356a05b665af6b7aba5c1d25083a57bd"
scope:
  - doc/feat/28-reviewable-workflow/spec.md
  - doc/feat/28-reviewable-workflow/design.md
  - doc/feat/28-reviewable-workflow/slices/01-review-loop.md
```

The maintainer instructed: "Start slice 01’s first iteration using the current
candidate; present the template and example before continuing." This authorizes
only [slice 01](slices/01-review-loop.md#proposed-iterations)'s first iteration:
a one-screen review artifact template and one worked discovery example, using
the applicable overall review and record contracts at the revision above.
Remaining iterations, tool adoption, and parallel reversal await later decisions.
The defining and executor roles use this same conversation; this is not an
independent session review.

Plan and completion condition:

1. Record this scoped approval and delivery state; check metadata, history and
   routes, then commit the handoff.
2. Place the candidate template in `feat-workflow.md` and a retrospective
   discovery example in an execution entry. Compare one legacy and one embedded
   journal record with a reproducible offline probe. Check content, ownership,
   links, unchanged approved contract bodies, and `make ci`, then commit.
3. Identify the delivered revision in the overview, check and commit that
   publication metadata, then push to draft PR #29 and present the artifact.
   Stop for maintainer review before any dependent iteration.

Estimated initial review: three minutes for the template and example; actual
maintainer feedback remains pending. This first example supplies partial
`F28-01:AC-1` evidence, not the complete multi-phase walkthrough or slice delivery.

Handoff validation: bounded metadata, approval scope, native identity, local
link and whitespace checks passed. Approved contract bodies remain unchanged,
and all earlier journal text is preserved. Full CI belongs to the artifact step.

## J-16: Approve relocated first step

```yaml
id: J-16
date: "2026-09-29"
kind: approval
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
revision: "dd0a9c16665bef9490b0a0d550b8f43767d2eb16"
scope:
  - doc/feat/28-reviewable-workflow/spec.md
  - doc/feat/28-reviewable-workflow/design.md
  - doc/feat/28-reviewable-workflow/slices/01-review-loop.md
```

The maintainer said, "yeah, lets adopt those changes", and instructed reversal,
planning amendment and replay in a slice PR to the feat. This records that
instruction at the amended hierarchy revision above, limited to relocating
`F28-01:STEP-1`'s existing template/example and establishing its review branches.
It does not authorize iteration 2 or approve the delivered template's contents.

Replayed the original approval commit with its unchanged J-13 record appended
after J-15. Updated mutable state to identify slice issue #30, branch
`feat/reviewable-workflow-slice-01` and its feat base. The original review-metadata
commit's purpose is replayed through new branch/PR handoffs; its obsolete
comparison range is retained in original Git history. Step delivery will replay
the original template/example commit on a child branch before review and merge.
The original order of numbered events is not a new identity; IDs stay reserved.

Validation: bounded metadata, event preservation, native identity and local-link
checks passed. `make ci` passed with 232 repository tests, 3 examples, type/import
checks, installed-wheel smoke and audit. Slice acceptance remains pending.
Defining and executor roles share the recorded native conversation.

## J-14: Deliver the review template and example

```yaml
id: J-14
date: "2026-09-29"
kind: execution
role: executor
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

Delivered the [candidate review artifact template](../../feat-workflow.md#review-artifact-template)
under [J-13's scoped approval](#j-13-approve-slice-01-iteration-1).
The following worked discovery example replays the earlier journal-identity
question against pinned records. Its decision was already made in
[J-12](#j-12-adopt-embedded-journal-metadata); this walkthrough evaluates how the
template presents that evidence.

**Outcome:** Demonstrate the discovery case for `F28-01:AC-1`: can one journal
entry identify its recording conversation without looking up a session alias?

**Inspect:** Compare
[J-11](https://github.com/msitarz/ataraxia/blob/406d2e61356a05b665af6b7aba5c1d25083a57bd/doc/feat/28-reviewable-workflow/journal.md#j-11-note-calldiff-for-future-review)
and [J-12](https://github.com/msitarz/ataraxia/blob/406d2e61356a05b665af6b7aba5c1d25083a57bd/doc/feat/28-reviewable-workflow/journal.md#j-12-adopt-embedded-journal-metadata)
at candidate `406d2e61356a05b665af6b7aba5c1d25083a57bd`.

**Evidence:** Hypothesis: embedded provider/thread metadata makes one entry
sufficient for identity lookup. Alternatives: alias plus registration, or repeated
native identity. Stop after inspecting one record of each form. The
[offline probe](#discovery-probe-for-the-example), run with Python 3.14.7, printed
`J-11: alias only; J-12: Codex UUID in entry`. J-11 needs another entry to resolve
S1; J-12 contains the provider and a valid UUID. The probe checks this bounded
structural property; it does not authenticate identity or validate general YAML.

**Consequences:** Embedded identity was accepted in J-12. Structural review keeps
the reusable template with its workflow owner and this evidence in the journal.
Approved contract bodies remain unchanged. The probe uses existing Git and
Python, and adds no dependency. General schema/link gates remain future work.

**Decision requested:** Does this field set expose enough context, evidence and
consequences for a short review? Accept it, request specific corrections, or defer.

**Next:** If accepted, propose iteration 2's continuation and material-change
guidance with worked boundary cases. Dependent continuation awaits approval.

**Review effort:** Estimated three minutes for the template and this entry point;
actual maintainer feedback is pending. Other phase examples and the full slice
acceptance walkthrough remain outstanding.

### Discovery probe for the example

Run from the repository root; the input is the pinned historical candidate:

```sh
uv run --no-sync python - <<'PY'
import re
import subprocess
from uuid import UUID

revision = "406d2e61356a05b665af6b7aba5c1d25083a57bd"
path = "doc/feat/28-reviewable-workflow/journal.md"
journal = subprocess.check_output(["git", "show", f"{revision}:{path}"], text=True)
legacy = journal.split("## J-11:", 1)[1].split("\n## J-", 1)[0]
embedded = journal.split("## J-12:", 1)[1].split("\n## J-", 1)[0]
assert "Session: S1" in legacy and "thread_id:" not in legacy
assert "  provider: codex\n" in embedded
thread = re.search(r'^  thread_id: "([^"]+)"$', embedded, re.M).group(1)
assert str(UUID(thread)) == thread
print("J-11: alias only; J-12: Codex UUID in entry")
PY
```

Iteration validation: the exact documented probe passed. Bounded checks passed
for 10 package documents, 39 scoped acceptance rows and 115 local links/anchors,
including the workflow owner. Checked the template/example fields, native entry
identity, approval scope, unchanged approved contract bodies and append-only
history. `git diff --check` and `make ci` passed with 232 repository tests,
3 examples, type/import checks, installed-wheel smoke and audit. Proposed
`make docs-check` has not been implemented. Maintainer review and independent
session review have not occurred; iteration 2 has not started.

## J-17: Replay the template on its step branch

```yaml
id: J-17
date: "2026-09-29"
kind: execution
role: executor
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

Replayed the template/example from
`efe5d17d06c5b1cd02bba593319ba92eb2b0449e` on
`feat/reviewable-workflow-slice-01-step-01`, based on slice revision
`9231d7164ec41835872bbd594b4e2b3770fbb1ce`. The first step's tracking lives
in [slice 01](slices/01-review-loop.md)'s frontmatter. It has
[issue #32](https://github.com/msitarz/ataraxia/issues/32), and its PR targets
the slice branch. The receiving slice has
[issue #30](https://github.com/msitarz/ataraxia/issues/30) and
[draft PR #31](https://github.com/msitarz/ataraxia/pull/31) to the feat branch.

Preserved J-14 exactly as historical execution evidence after the receiving
branch's records. Its original comparison and validation refer to that earlier
delivery. This entry and the overview own the relocation's current evidence and
review handoff. The reusable template is unchanged; the amended specification
and design retain the scope approved in J-16. No new delivery iteration is added.

Validation: the exact documented probe passed. Bounded checks passed for 10
proposal documents, 42 scoped acceptance rows and 125 local links/anchors,
including unchanged J-13/J-14 records, the original template, approved contract
bodies and the registered step's parent/base identity. `git diff --check` and
`make ci` passed with 232 repository tests, 3 examples, type/import checks,
installed-wheel smoke and audit. The proposal's `make docs-check` remains
unimplemented; these migration checks do not claim its delivery.
Maintainer review is pending; no PR is merged, and iteration 2 has not started.

## J-18: Clarify visual review options

```yaml
id: J-18
date: "2026-09-29"
kind: execution
role: executor
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

The maintainer requested explicit permission to use Mermaid when applicable,
especially in Markdown documentation, in the review template's visual note.
Preserve their existing addition of GitHub to the review tools in that paragraph.
This corrects the current artifact within
[step PR #33](https://github.com/msitarz/ataraxia/pull/33); it does not start
another delivery step or change the approved specification/design contracts.

Plan: update the owning visual note, check the bounded change and preserved
history, run required publication CI, and commit. Then advance the overview's
review revision in a checked metadata commit and push to the same step PR.

Validation: bounded note scope, native entry identity, unchanged contracts and
journal history, and 49 local links/anchors passed. `git diff --check` and
`make ci` passed with 232 repository tests, 3 examples, type/import checks,
installed-wheel smoke and audit. Earlier journal entries remain unchanged;
maintainer review and dependent continuation remain pending.

## J-19: Authorize continuation after step 1 merge

```yaml
id: J-19
date: "2026-09-29"
kind: approval
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
revision: "dd0a9c16665bef9490b0a0d550b8f43767d2eb16"
scope:
  - doc/feat/28-reviewable-workflow/spec.md
  - doc/feat/28-reviewable-workflow/design.md
  - doc/feat/28-reviewable-workflow/slices/01-review-loop.md
```

The maintainer said, "ok, i merged that PR, lets move to the next step".
Verified [PR #33](https://github.com/msitarz/ataraxia/pull/33) is merged into
the slice at `588cde5ba881b6e20d1dfc0d558ae710e3b6d264`; fetched that revision
and created `feat/reviewable-workflow-slice-01-step-02` from the updated slice.
This authorizes only `F28-01:STEP-2`: continuation, material-change and step/slice
PR guidance with boundary examples. Contract bodies remain at the revision above.
The step has [issue #34](https://github.com/msitarz/ataraxia/issues/34).
The same conversation performs defining and executor roles; no independent
session review is claimed. Later steps and tool adoption remain unapproved.

Plan and completion condition:

1. Record the verified merge, scoped instruction and step tracking; check
   identity, metadata, unchanged contracts and history, then commit the handoff.
2. Replace conflicting single-branch guidance at its owner, route contribution
   guidance to that owner, and record a compact boundary walkthrough. Check
   consistency, links and history, run `make ci`, and commit the artifact.
3. Pin the review range in the overview, publish a draft step PR to the slice,
   verify its actual base/head, and update tracking. Stop for maintainer review
   before step 3; corrections stay in this step PR.

Initial review estimate: four minutes for the changed guidance and boundary table;
actual maintainer feedback remains pending. This advances `F28-01:AC-2` and
`F28-01:AC-5`; the full slice acceptance walkthrough is still outstanding.

Handoff validation: bounded checks passed for 10 documents, 42 scoped acceptance
IDs and 97 local links/anchors, including native identity, preserved journal and
contract bodies, step tracking and updated slice ancestry. The merge is observed
separately from the maintainer's explicit authorization to continue.

## J-20: Deliver continuation and branch gates

```yaml
id: J-20
date: "2026-09-29"
kind: execution
role: executor
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

**Outcome:** Deliver `F28-01:STEP-2` under [J-19](#j-19-authorize-continuation-after-step-1-merge),
advancing `F28-01:AC-2` and `F28-01:AC-5`. Replace the old single-branch execution
instruction with [delivery branches and review gates](../../feat-workflow.md#delivery-branches-and-review-gates),
including a visual companion and material-change rules. Contribution guidance
routes to that owner. Earlier specifications and journal entries remain intact.

**Inspect:** Review the changed workflow paragraphs and the boundary table below.
The overview will pin the delivered revision against slice merge
`588cde5ba881b6e20d1dfc0d558ae710e3b6d264`. The existing seven artifact fields and
Mermaid visual note remain unchanged; the template's pending-review label is
removed after the maintainer's step 1 merge.

### Boundary walkthrough

These are illustrative instruction/state combinations, checked against the owning
guidance; they do not authenticate an approval or execute an automated workflow.

| Situation | Expected agent action |
| --- | --- |
| “Accept revision A”; its step PR is still open | Record scoped approval; wait for reviewed merge before dependent continuation |
| “Correct the Mermaid note” within the approved scope | Correct, check, commit and push on the same step PR; present the changed revision |
| Checks pass, with no maintainer response | Keep the review pending; start no dependent step |
| Approved A gains a changed contract in B | Pause affected implementation; publish B's planning change for explicit approval |
| The step PR targets the feat rather than the slice | Correct the target and verify checks against the actual parent before merge |
| The current revision is approved and the next outcome authorized, but merge is pending | Prepare only independent authorized work; wait for merge before the dependent step |
| The step is merged, with no authorization for the next outcome | Record integration; await the next instruction |
| The step is merged and “move to the next step” authorizes the agreed next outcome | Verify the merge, fetch the updated slice, and create the next step's issue/branch/PR |

The final row is also observed in this delivery: PR #33 merged at the recorded
slice revision, followed by the maintainer's continuation instruction and issue #34.
The remaining rows are a document walkthrough, not completed checker fixtures.
Full acceptance and the later two-step integration evaluation remain pending.

**Evidence:** Bounded checks passed for 10 documents, 42 scoped acceptance IDs and
104 local links/anchors, including native identity, preserved contracts/history,
tracking, and the eight illustrative cases against the owning rules.
`git diff --check` and `make ci` passed with 232 repository tests, 3 examples,
type/import checks, installed-wheel smoke and audit. The new Mermaid view awaits
maintainer visual review. Future `make docs-check` needs tracking,
approval/revision and history fixtures for these cases, plus an explicit GitHub
adapter for actual targets and merge evidence. No checker or library is adopted
in this step.

**Consequences:** Procedures stay with the workflow owner. Contribution defaults
delegate feat parent selection there. No application code, dependency or
architectural decision changes; approved proposal bodies remain unchanged.

**Decision requested:** Review the proceed/stop rules and boundary outcomes;
accept them or request corrections in this step PR.

**Next:** After reviewed merge and explicit continuation, deliver step 3's package
template and ownership routes. Step 3 has not started.

**Review effort:** Estimated four minutes for the guidance and this table;
actual maintainer feedback remains pending. The defining and executor roles share
this conversation; no independent session review is claimed.

## J-21: Authorize document template delivery

```yaml
id: J-21
date: "2026-09-29"
kind: approval
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
revision: "dd0a9c16665bef9490b0a0d550b8f43767d2eb16"
scope:
  - doc/feat/28-reviewable-workflow/spec.md
  - doc/feat/28-reviewable-workflow/design.md
  - doc/feat/28-reviewable-workflow/slices/01-review-loop.md
```

The maintainer said, "ok i merged, lets move to the next step". Verified
[PR #35](https://github.com/msitarz/ataraxia/pull/35) merged into the slice at
`78a67e709c987d090c98b1aec671d0983e4f5811`, fetched that revision and created
`feat/reviewable-workflow-slice-01-step-03` from the updated slice.
This authorizes only `F28-01:STEP-3`: package templates, ownership routes and
Mermaid companions, using the unchanged candidate contract bodies above.
The step has [issue #36](https://github.com/msitarz/ataraxia/issues/36).
Step 4, tool adoption and checker implementation remain pending. Defining and
executor roles share this native conversation; no independent review is claimed.

Plan and completion condition:

1. Record the verified merge, scoped instruction and step tracking; check
   native identity, metadata, preserved contracts/history and ancestry, then
   commit the handoff.
2. Add one reusable template document for metadata and predictable document
   bodies; update ownership and workflow routes. Walk through the current grouped
   feat and a compact child slice, check examples and local links, run `make ci`,
   and commit the artifact. Preserve all historical slices and journal records.
3. Pin the review range and navigation, publish a draft step PR to the slice,
   verify its actual parent/head and update tracking. Stop for maintainer review
   before step 4. Corrections stay in this step PR.

Initial review estimate: four minutes for the formats, ownership map and worked
routes; actual feedback remains pending. This advances `F28-01:AC-1` and
`F28-01:AC-3`; full slice acceptance remains pending.

Handoff validation: bounded checks passed for 10 documents, 42 scoped acceptance
IDs and 110 local links/anchors, including native identity, metadata, preserved
contracts/history and updated slice ancestry. Observed merge and explicit
continuation instruction remain separate evidence.

## J-22: Deliver document formats and owner routes

```yaml
id: J-22
date: "2026-09-29"
kind: execution
role: executor
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

**Outcome:** Deliver `F28-01:STEP-3` under [J-21](#j-21-authorize-document-template-delivery),
advancing `F28-01:AC-1` and `F28-01:AC-3`. The
[templates](../../feat-templates.md) provide metadata profiles and predictable
document bodies; [ownership](../../documentation.md#feat-documents) separates
current state, contracts, proposed design and append-only history. Workflow and
glossary routes point to these shared owners. Term meanings are preserved.

**Inspect:** Review the field profiles, specification and journal scaffolds, and
owner map. The overview will pin this artifact against slice merge
`78a67e709c987d090c98b1aec671d0983e4f5811`. Example values are illustrative,
not registered feats, acceptance criteria, sessions or approvals.

### Package navigation walkthrough

Agent inspection of existing documents, rather than a maintainer review or
complete conformance migration:

| Case | Route and observed ownership |
| --- | --- |
| Grouped feat | [README](README.md) → [spec](spec.md) for `F28` contracts, [design](design.md#visual-overview) for proposed relationships, [journal](#j-21-authorize-document-template-delivery) for scoped instruction/native identity, then the selected slice |
| Compact child | [Slice 04](slices/04-acceptance-evidence.md) owns `F28-04` criteria and its local plan; its links reach the parent contracts/design and parent journal without another README, design or journal file |

The existing [specification visuals](spec.md#visual-overview) and
[design visuals](design.md#visual-overview) demonstrate the respective behavior
and relationship views. Existing approved bodies keep their headings; they are
examples of the model, not a claim that they match every new scaffold heading.
The new ownership diagram and copied-template views await maintainer visual review.

**Evidence:** Bounded checks passed for 10 documents, 42 scoped acceptance IDs and
171 local links/anchors, including native identity, parent/base tracking and
preserved contracts/history. Frontmatter and nested Markdown/YAML examples parse;
illustrative IDs stay outside the live index. `git diff --check` and `make ci`
passed with 232 repository tests, 3 examples, type/import checks, installed-wheel
smoke and audit. Mermaid rendering awaits maintainer visual review.
Future `make docs-check` should
compose investigated rumdl hygiene/link support, kind-specific metadata and
heading checks, namespace/history rules and route findings. Language checks await
the STE investigation; no checker or dependency is adopted here.

**Consequences:** Formats have one linked owner with a specific reading trigger;
`AGENTS.md` stays a routing entry point. Compact children keep one contract file,
larger outcomes add files only for distinct responsibilities. Approval remains
human evidence; schemas cannot authenticate it. Historical records stay intact.

**Decision requested:** Accept the document shapes and metadata/ownership boundaries,
or request corrections within this step PR.

**Next:** After reviewed merge and authorization, deliver step 4's structural and
discovery/promotion/migration guidance. Step 4 has not started.

**Review effort:** Estimated four minutes for the format choices and owner map;
actual maintainer feedback remains pending. Defining and executor roles share
this conversation; no independent session review is claimed.


## J-23: Propose overhead reduction

```yaml
id: J-23
date: "2026-09-29"
kind: decision
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

**Outcome:** The maintainer requested another slice 01 step for the overhead
findings, switched effort to medium, then said "proceed with the overhead-reduction
step to slice 01". Verified PR #37 merged at
`764e3e1f4cad43482c1847f78b88bc9153913bba`; step 5 starts from that updated slice
and precedes unstarted step 4 without renumbering. [Issue #38](https://github.com/msitarz/ataraxia/issues/38)
tracks this planning amendment. Changed contracts require review before adoption;
previous approvals do not automatically cover them.

**Inspect:** [Slice amendment](slices/01-review-loop.md#overhead-reduction-amendment),
[contract](spec.md#execution-effort-and-validation), and
[design](design.md#bounded-execution-and-evidence-reuse). The step PR identifies
its actual head and comparison base. No active guidance, tooling or CI change.

**Evidence:** The local step 3 recording spans 28 minutes 13 seconds, with 38
model requests, one compaction, one full local CI run, nine temporary-check runs,
four commits and 28 GitHub CLI attempts including six failed requests. Outer tool
calls occupied about 77 seconds; tests took 32.5 seconds. Input caching was already
about 95%; this cannot establish an exact weekly-allowance cost. These observations
support reducing repeated reasoning and bookkeeping, not removing cheap whitespace
checks or weakening merge evidence.

Plan: draft this small amendment; inspect links, metadata, preserved history and
the two cases below; run currently required CI once; commit, publish and register
the real PR in one tracking follow-up. Reuse that remote result and update only
the immediate parent pointer. Metadata, scoped IDs, local links and preserved
history passed. `git diff --check` and one `make ci` run passed: 232 tests,
3 examples, type/import checks, installed-wheel smoke and audit. The parser
inspection needed a cache permission retry; no framework was added. Trial timing
is reported in the PR at publication, rather than creating another journal commit.

| Walkthrough | Proposed rule outcome |
| --- | --- |
| Only navigation changes; runtime inputs/configuration/tools/environment match earlier evidence | Rerun affected docs checks; identify the earlier runtime result and why it applies; full current-head merge CI still required |
| Code, tests, checker logic or a relevant dependency changes | Invalidate dependent evidence and run applicable focused/broader checks; do not claim reuse solely because a path looks like documentation |

These are rule inspections, not executed cache or selection fixtures. Proposed
checkers: investigated Markdown/link tools; later selection/provenance fixtures
that reject stale inputs and distinguish reused, pending and unrun checks.
No temporary framework, persistent cache or new skill is adopted.

**Consequences:** The proposed budget is a planning signal; existing approval,
merge and scope gates stand. Publication tracking stays with its owner, with
links above it. Medium effort is verified from runtime metadata for this trial.

**Decision requested:** Accept or correct the validation and publishing amendment.
**Next:** After reviewed merge and explicit authorization, deliver the adopted
owner guidance as a separate bounded step. Structural step 4 remains pending.
**Review effort:** Estimated three minutes; actual maintainer feedback pending.


## J-24: Authorize overhead guidance

```yaml
id: J-24
date: "2026-09-29"
kind: approval
role: defining
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
revision: "5d081802630fce38dbaeee3501665ab15636cc34"
scope:
  - doc/feat/28-reviewable-workflow/spec.md
  - doc/feat/28-reviewable-workflow/design.md
  - doc/feat/28-reviewable-workflow/slices/01-review-loop.md
```

The maintainer said "merged, lets move on to the next step and see how this new
overhead reduction workflow actually works." Verified [PR #39](https://github.com/msitarz/ataraxia/pull/39)
merged into the slice at `004a6ba66d7422284d071a00a5bfa01f3cbd1f93`.
The approved contract bodies above are the reviewed amendment revision; the
instruction authorizes delivery of their owner guidance, not step 4 or a new
checker/cache. Same native conversation performs defining and execution roles.

Plan: register step 6 from the updated slice; deliver the two guidance owners
and a navigation-versus-code evidence walkthrough; check affected routes and
history, publish a draft PR, then register its actual link once. Full CI on
that review head remains required before merge. Initial review estimate:
four minutes; actual feedback pending.

## J-25: Deliver overhead guidance

```yaml
id: J-25
date: "2026-09-29"
kind: execution
role: executor
session:
  provider: codex
  thread_id: "01a0ec64-dc47-77f2-940e-a825c88761f5"
```

**Outcome:** Advance `F28-01:AC-6` by routing draft validation, evidence reuse
and full current-head merge CI through [contribution guidance](../../../CONTRIBUTING.md#validation-selection).
[Workflow guidance](../../feat-workflow.md#stepwise-changes-and-commits) owns
the execution signal, remote observation and publishing boundaries. No Makefile,
CI, hook, dependency, cache or application change.

**Inspect:** These two owner sections and the cases below. The step PR names the
actual head and comparison base; the overview links to it after publication.

| Input change | Required observation |
| --- | --- |
| Navigation or non-executable prose only | Affected docs checks and hooks locally; earlier runtime result may be cited only with unchanged inputs/tools/environment; full CI must pass on the latest review head before merge |
| Code, tests, executable example, checker logic or relevant dependency | Invalidate dependent evidence; run affected focused or broader local checks; full current-head CI still gates merge |

**Evidence:** Bounded inspection passed for 12 relevant documents, 43 scoped
criteria and 128 local links/anchors, plus preserved approved bodies, journal
history and native identity. Three incorrect relative paths were corrected
during inspection. `git diff --check` and the normal commit hooks passed.
Local full CI was not run for this documentation-only draft. GitHub CI must
pass on the latest PR head before merge. The examples inspect the guidance,
not an implemented selection/cache fixture.

**Consequences:** Drafts can be opened while CI is pending, and merge readiness
still requires actual current-head evidence. A ten-minute target prompts a
smaller outcome proposal without waiving checks or abandoning authorized work.
Tracking stays at the current owner; ancestor records link to it.

**Decision requested:** Accept or correct the validation and publishing rules.
**Next:** After reviewed merge and explicit authorization, continue the remaining
slice 01 outcome; step 4 is still unstarted. **Review effort:** Estimated four
minutes; actual feedback pending.
