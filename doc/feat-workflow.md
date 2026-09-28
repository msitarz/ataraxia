# Feat slice workflow

Read this file in full when defining, implementing, or reviewing a
[feat slice](ubiquitous-language.md). It owns the delivery workflow and
specification-writing guidance. Use [documentation ownership](documentation.md) for placement rules,
[CONTRIBUTING.md](../CONTRIBUTING.md#make-targets) for validation, and the
[ADR workflow](adr-workflow.md) for architectural decisions.

## Define and publish for specification review

After reading the glossary and relevant context, inspect the current branch,
working tree, and existing issues/PRs. Reuse a branch already owning the work.
Otherwise, create a local branch from the applicable PR base before writing the
specification. Preserve unrelated work; don't base unrelated work on an existing
feat branch. Explicit task instructions determine the base, otherwise use
[contribution guidance](../CONTRIBUTING.md#submitting-a-change).

Name branches `feat/<short-kebab-case-name>`, for example
`feat/parallel-shard-computation`. Validate with
`git check-ref-format --branch <name>`. No issue number is required because the
branch comes first. Existing branches need not be renamed.

Create or reuse an issue before drafting the specification or doing non-trivial
architectural work. Follow [Issue messages](#issue-messages). State whether the
issue's outcome is an accepted specification or an implemented capability. Write
the specification in `doc/feat/`, link the issue, follow
[documentation ownership](documentation.md), and use the
[ADR workflow](adr-workflow.md) when decisions are needed.

Once the planning documents are reviewable, run `make ci`, commit and push, and
open a draft PR against the applicable base. Add links between the issue, feat
slice, and PR. Use `Refs #N` for partial delivery, including specification-only
work on an implementation issue; use `Closes #N` only when merging completes the
issue. GitHub closing keywords apply to PRs targeting the default branch.

Stop at manual specification review. The maintainer must explicitly approve
execution of the identified specification revision before implementation starts.
Record the approval and revision in the handoff. Silence, passing checks, an
agent review, or creating a PR is not approval. An explicit instruction to
execute an already reviewed scope is approval; don't ask for it again.

## Execute the approved scope

The executor session may be a later session using a different model. It reads
the glossary, this workflow, the approved specification, applicable ADRs, and the
handoff before implementing. If approval is missing or ambiguous, resolve that
gate with the maintainer before execution. Continue independent preparation.

Implement the approved scope on the same branch and PR. Run focused checks and
the required repository checks, record results and limitations in the feat slice,
and update the issue with the stage and links to current evidence. Keep the issue
short; don't copy the specification or test results into a second record.
Commit and push checked changes so the PR reflects the delivered implementation.

If findings require changing scope, acceptance criteria, interfaces, or another
material contract, update the specification and applicable ADRs, push the planning
revision, and return to manual specification review before implementing that
design. Routine corrections within approved scope don't need a new specification
approval. Report unresolved problems rather than weakening completion conditions.

## Review and revise

After execution, stop for manual implementation review and review by the defining
session. The defining session checks the delivered diff, acceptance examples,
validation evidence, and any specification changes against the approved scope.
Report findings according to the glossary's session responsibilities.

Record the commit each review covers and its outcome in the handoff or a linked
issue/PR review. The executor addresses proposed changes, reruns relevant checks
and `make ci`, updates evidence, and pushes to the same PR. Repeat the affected
reviews until findings are resolved. Check documentation ownership and duplication
alongside contracts and validation; follow
[documentation review](documentation.md#review). Review the changes from later pushes;
approvals of earlier commits do not automatically approve new changes. Material
contract changes also return to specification approval.

Keep the PR draft while required approvals or reviews are outstanding. Once
completion conditions, checks, manual review, and defining-session review pass,
record that evidence and mark it ready for the maintainer's final decision.
The maintainer manually merges accepted work or closes the PR without merging.
Agents do neither and don't enable automatic merging.

Specification-only delivery follows the manual specification gate and ends when
the maintainer accepts that planning outcome. It doesn't require implementation
review of code that wasn't delivered or validate a future implementation. The
maintainer still makes the final GitHub decision.

## Specification status

A specification is `proposed` before execution, `in progress` during delivery,
and `validated` after its acceptance criteria and required checks pass. State
whether completion delivers an accepted specification or implemented behavior.
Validation does not authorize execution or merging; approvals and pending work
belong to the handoff stage.

## Roles and handoffs

Use the glossary's [defining session and executor session](ubiquitous-language.md)
responsibilities. Identify them with a resumable link or a name the maintainer
can recognize. If the defining session is unavailable, the maintainer explicitly
designates a replacement reviewer; the executor doesn't waive that review.
If roles share a session, disclose that fact rather than claiming an independent
review. Respect any requirement from the maintainer for separate sessions.

Keep a small handoff section in the feat slice containing:

- Current workflow stage and the defining/executor sessions.
- Approved specification commit and evidence of the maintainer's approval.
- Branch, issue, PR, and applicable ADR links.
- Current validation evidence or links to it, including limitations.
- Unresolved findings and reviews with the commits they cover.

Keep the handoff current at each gate and session transfer. A new session should
be able to continue from these records without relying on conversation memory.
Keep specification status consistent with the evidence and the handoff stage.

## Failures and boundaries

Follow [validation procedure](../CONTRIBUTING.md#make-targets) if network
access prevents `make ci`. Disclose missing checks and keep incomplete work draft.
If GitHub access fails, report it, continue useful local work, and add external
links once access returns. Don't claim an issue or PR exists without verifying
it. If the missing issue blocks architectural work under the ADR workflow,
finish local preparation without implementing the affected design.

Small unrelated fixes or documentation edits need neither a feat slice nor this
workflow. Non-trivial work still needs an issue under contribution guidance;
substantive architectural decisions still follow the ADR workflow.

## Issue messages

Use descriptive sentence-case titles naming the problem or desired capability,
such as `Add parallel execution across shards`. No type prefix is required;
classify with existing labels where useful.

Use the [Markdown issue template](../.github/ISSUE_TEMPLATE/work-item.md) as the
authoritative body format for both manual and agent-created issues. Follow its
Problem, Outcome, and Links prompts; add scope boundaries or open questions when
they affect the decision. Keep the issue a short tracking record: the feat slice
owns detailed scope, acceptance examples, and validation,
while ADRs own architectural decisions. Link those records instead of copying
their specifications into the issue. Add links as artifacts become available.

For CLI creation, fill the template's body into a temporary Markdown file and
pass it with `gh issue create --title ... --body-file <file>`; omit the template's
front matter and instructional comments. The template guides content but doesn't
enforce it across every GitHub creation path.

## Writing feat slices

Write proportional specifications in `doc/feat/` using short prose and examples;
no user-story formula or Gherkin is required. Follow the gates above,
[documentation ownership](documentation.md), and the [ADR workflow](adr-workflow.md).
Keep local contracts and evidence here; link to shared meanings, architectural
rationale, and general procedures instead of copying them.

- Lead with the problem, code-verified current behavior, and observable outcome. State status (`proposed`, `in progress`, or `validated`); link issues and applicable ADRs as decisions emerge.
- Scope a small usable increment across necessary components; split larger work by scenario or capability. State non-goals and dependencies; separate preparatory refactors and experiments. Plan short, tested steps that preserve a working path and provide early feedback; make scope/contract changes explicit.
- Give acceptance examples with preconditions, inputs, action, and expected outputs or side effects. Cover correctness, failures, boundaries, and behavior to preserve through observable contracts. Identify focused, integration, or CLI checks; refine scenarios as needed. Separate validation plans from results, recording evidence and limitations. Mark validated only after acceptance criteria and required repository checks pass.
- Separate required interfaces, ordering, compatibility, and resource ownership from provisional design. Sketch only enough internals to establish feasibility and consequential tradeoffs.
- Name assumptions, risks, and open questions. Test uncertainty that could invalidate the approach with a bounded experiment: expected result and evidence that would challenge it. Record findings and revise the plan; an experiment is not a completed feature.
- Support performance claims with a baseline, representative workload, measurement method, and success criterion.

Examples such as successful results matching across execution modes or an
invalid CLI argument preserving an existing output file express observable
contracts. They are illustrative, not requirements for every slice. Executor
classes and scheduling helpers belong in design notes unless architectural
impact warrants an ADR.

Background: [Thoughtworks](https://www.thoughtworks.com/en-au/insights/e-books/modern-data-engineering-playbook/delivery-planning-principles), [Fowler](https://martinfowler.com/bliki/FeatureDevotion.html), [Beck](https://newsletter.kentbeck.com/p/canon-tdd), [Farley](https://www.davefarley.net/?page_id=50).
