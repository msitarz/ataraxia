# Feat slice branch and PR workflow

Status: validated

Issue: [22](https://github.com/msitarz/ataraxia/issues/22)

PR: [23](https://github.com/msitarz/ataraxia/pull/23)

## Problem and outcome

Before this change, agent guidance used “feature slice” alongside trading Features
and referred to a `doc/feature/` directory that didn't exist. Contribution guidance
required branches and PRs against `master`, but there was no naming convention or
issue template, and only non-trivial work explicitly required an issue.

Adopt the [feat slice](../ubiquitous-language.md) vocabulary and one workflow from
local branch through issue, specification, and linked PR. Completion means the
workflow is documented, its template is usable, and this change has exercised the
workflow with passing repository checks.

## Scope and steps

Define the term in the glossary, write the workflow in `AGENTS.md`, align
`CONTRIBUTING.md`, and add a Markdown issue template. No runtime behavior changes,
new architectural decisions, or mandatory issue automation are included. Existing
branches need not be renamed. Small unrelated fixes and documentation edits need
neither a feat slice nor an issue unless otherwise non-trivial.

Use a local `feat/agent-workflow` branch, create the issue, write this specification,
and update guidance and the template. Run `make ci`, commit and push, open a draft
PR against `master`, and add links to the issue. Review the resulting artifacts
and mark the PR ready when completion conditions pass.

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
- A ready-for-review PR satisfies the delivery's completion conditions and
  required checks. An implemented capability cannot be called validated merely
  because its specification was reviewed.
- An unrelated current branch or dirty checkout is inspected before switching;
  unrelated work is preserved. Failed GitHub access is reported, local work can
  continue, and no issue or PR is claimed to exist without a returned URL.
- Contribution guidance links to the authoritative workflow; issue instructions
  reuse the checked-in template. No current guidance uses the previous term or
  nonexistent specification path.

## Validation plan and evidence

Inspect terminology, relative links and anchors, template front matter, and the
diff for consistency. Validate the branch name with
`git check-ref-format --branch feat/agent-workflow`. Run `make ci`, including the
existing checks, tests, examples, installed-wheel smoke test, and audit. Inspect
the created issue and PR for body structure, branch/base, and issue references.

Branch and issue creation have succeeded. `make ci` passed: 142 tests, 3 example
tests, 97.12% branch-inclusive coverage, strict types and expected negative cases,
architecture checks, installed-wheel smoke test, and audit of 38 packages. The
tracked-file hooks also passed after staging the new files. Relative links and
anchors, template front matter and body headings, terminology, branch naming,
and whitespace checks passed. Draft PR 23 was verified to use
`feat/agent-workflow` as its head, `master` as its base, and issue 22 as its closing
reference. The issue's Problem, Outcome, and Links body links back to the feat
slice and PR. The unrelated parallel-execution branch was preserved. This
exercises the new-work path; reuse, partial delivery, and failure handling were
checked for consistency in the guidance rather than creating extra GitHub items.

The issue template will appear in GitHub's issue chooser after merging into
`master`; before then, its Markdown body is used through the CLI. This is
guidance, not enforcement of issue content through every GitHub creation path.
