# Feat slice branch and PR workflow

Status: validated

Issue: [22](https://github.com/msitarz/ataraxia/issues/22)

PR: [23](https://github.com/msitarz/ataraxia/pull/23)

This validated slice records its delivery scope and evidence. Current guidance
is routed through [AGENTS.md](../../AGENTS.md); later ownership changes are
recorded in the [documentation cleanup slice](documentation-ownership.md).
The requirements below describe this historical delivery, not today's file layout.

## Problem and outcome

Before this change, agent guidance used “feature slice” alongside trading Features
and referred to a `doc/feature/` directory that didn't exist. Contribution guidance
required branches and PRs against `master`, but there was no naming convention or
issue template, and only non-trivial work explicitly required an issue.

Adopt the [feat slice](../ubiquitous-language.md) vocabulary and one workflow from
local branch through issue, specification, and linked PR. The first version lets
agents continue from specification directly into execution and keeps the full
workflow in `AGENTS.md`. The maintainer has approved revising it to require manual
specification approval, manual implementation review, and review by the defining
session, with durable handoffs between sessions.

Completion means the workflow lives in `doc/feat-workflow.md`, related guidance
and the issue template agree, required checks pass, and the revised PR is pushed
for manual review. Validation does not imply either manual approval gate passed.

## Scope and steps

Define the terms in the glossary, keep one routing instruction in `AGENTS.md`,
move workflow and specification-writing guidance into `doc/feat-workflow.md`,
align `CONTRIBUTING.md`, and reuse the Markdown issue template. No runtime changes,
new architectural decisions, or mandatory issue automation are included. Existing
branches need not be renamed. Small unrelated fixes and documentation edits need
neither a feat slice nor an issue unless otherwise non-trivial.

Reuse `feat/agent-workflow`, issue 22, and PR 23. Record the maintainer's approval
of the review-gate and extraction revisions, update guidance and the template,
run `make ci`, commit and push, and update the issue and PR. Leave the PR draft
while final manual review is outstanding; the maintainer merges or closes it.

## Acceptance examples

- Starting a new feat slice from a clean checkout creates
  `feat/<short-kebab-case-name>` from the applicable PR base before writing its
  specification, even when delivery is specification-only. An issue number is
  not needed to name the branch. A branch already owning the work is reused.
- An existing issue covering the outcome is reused. Otherwise, opening an issue
  uses a descriptive sentence-case title and a body with Problem, Outcome, and
  Links. Links are added as artifacts become available; detailed acceptance
  examples remain authoritative in the feat slice.
- Given a committed, checked, and pushed specification plus an issue, a draft PR
  targets `master` and references that issue. `Refs #N` leaves implementation
  work open after a specification-only merge; `Closes #N` is used only when
  merging completes the issue's outcome.
- After a checked planning document is pushed, the defining session stops for
  explicit manual specification approval. A later executor session reads the
  approved revision and handoff before implementing. Passing checks alone does
  not permit execution or merging.
- If execution reveals a material scope or contract change, the revised
  specification is pushed for renewed manual approval before implementing that
  design. Routine fixes within approved scope stay with the executor session.
- After execution, the issue links to updated evidence and the maintainer and
  defining session review the implementation at a recorded commit. Findings
  return to the executor session, which fixes, checks, and pushes to the same PR.
  Later pushes require review of their changes; earlier approvals don't silently
  carry over. If the defining session is unavailable, the maintainer names a
  replacement reviewer.
- Specification status and workflow stage are separate. A validated feat slice
  can still await manual review. Agents leave merging and closing to the
  maintainer; specification-only delivery can't validate future implementation.
- An unrelated current branch or dirty checkout is inspected before switching;
  unrelated work is preserved. Failed GitHub access is reported, local work can
  continue, and no issue or PR is claimed to exist without a returned URL.
- `AGENTS.md` routes only defining, executing, and reviewing feat slice work to
  the separate workflow. General code, commit, validation, and ADR rules remain
  there. Contribution guidance and glossary links resolve to the extracted file,
  and issue instructions reuse the checked-in template.

## Handoff

- Stage: awaiting manual implementation review; PR remains draft.
- Defining and executor session: this conversation, as requested by the
  maintainer. These roles share a session for this documentation change; no
  independent session review is claimed.
- Approved specification baseline: `2abb74b`, with the review-gate and extraction
  revisions approved by the maintainer's instruction, “adopt these changes and
  push so I can review the PR.” This authorizes execution here, not merging.
- Branch, issue, and PR: `feat/agent-workflow`, issue 22 and PR 23 linked above.
- Validation evidence: recorded below; checks for the revised scope passed.
- Reviews: manual implementation review pending; defining-session findings will
  identify the delivered commit in the issue. No unresolved findings yet.

## Validation plan and evidence

Inspect terminology, relative links and anchors, template front matter, and the
diff for consistency. Validate the branch name with
`git check-ref-format --branch feat/agent-workflow`. Run `make ci`, including the
existing checks, tests, examples, installed-wheel smoke test, and audit. Inspect
the created issue and PR for body structure, branch/base, and issue references.

For the initial delivery at `2abb74b`, `make ci` passed: 142 tests, 3 example
tests, 97.12% branch-inclusive coverage, strict types and expected negative cases,
architecture checks, installed-wheel smoke test, and audit of 38 packages. The
tracked-file hooks also passed after staging the new files. Relative links and
anchors, template front matter and body headings, terminology, branch naming,
and whitespace checks passed. Draft PR 23 was verified to use
`feat/agent-workflow` as its head, `master` as its base, and issue 22 as its closing
reference. The issue's Problem, Outcome, and Links body links back to the feat
slice and PR. The unrelated parallel-execution branch was preserved. This
exercised the new-work path. The revised scope reuses these artifacts; review
gates, cross-session handoffs, partial delivery, and failure handling were
checked for consistency in the guidance rather than creating extra GitHub items
or claiming that a future manual review has occurred.

For the review-gate and extraction revision, `make ci` passed again with the same
142 tests, 3 example tests, 97.12% coverage, and successful type, architecture,
installed-wheel, and audit checks. All 53 relative links and anchors, the issue
template, conditional routing, terminology, and whitespace checks passed. PR 23
was returned to draft for the outstanding manual review. The defining session
reviewed the guidance against the approved scope; its delivered commit and
findings are recorded in the linked issue after committing.

The issue template will appear in GitHub's issue chooser after merging into
`master`; before then, its Markdown body is used through the CLI. This is
guidance, not enforcement of issue content through every GitHub creation path.
