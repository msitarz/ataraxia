# Orchestrator handoffs

Read when acting as orchestrator for repository changes.

## Roles and delegation

The orchestrator owns scope, planning, read-only investigation, and independent
review and evidence assessment. The executor makes the bounded changes and
returns the artifact and evidence; it works directly within scope and does not
recursively delegate the same task.

For post-merge Work cleanup, hand off to the separate operational `cleaner`
subagent after the maintainer confirms the PR merged. Route it through
[branch-cleanup guidance](branch-cleanup.md) with the PR, branch, worktree,
reviewed head, and merge commit IDs. The maintainer authorizes Luna at medium
effort for this role only; general leaf-executor model policy is unchanged.
Review the cleaner's concise report instead of repeating its operations, and
serialize cleanup with worktree creation and other shared Git mutations.

For a Work tree, the orchestrator that owns a Work node with children owns
planning and integration for that subtree and manages its immediate child
agents. Delegate each leaf directly to the executor; the
leaf's owning parent reviews it. A child node with children has its own
orchestrator owner for that subtree. Each leaf has one responsible orchestrator;
do not add a dedicated wrapper around a leaf by default. Work tree nodes
mark responsibility boundaries, not required runtime layers. Parent and
subtree reviews own integration and interfaces, and reuse leaf evidence
instead of repeating a full leaf review. Schedule work by dependency readiness,
available concurrency, and expected shared edits rather than launching the
entire tree at once. Do not invent intermediary Work nodes solely to justify
runtime layers.

After exact-artifact and description review and acceptance assessment, hand
mechanical publication to the separate operational `publisher` with
[its owner](publisher.md), worktree, exact reviewed commit, approved title and
description file plus a digest or immutable copy, and existing PR when updating.
Include authorized repository/base overrides and, for a rewrite, the expected
remote commit captured before rebase. The orchestrator retains publication
accountability, final-CI assessment, and maintainer handoff; assess the
publisher's returned publication state and blockers.

Use GPT-6.1 Sol at low reasoning effort for every leaf executor.
This includes Investigation and empirical evaluation leaves as well as
implementation leaves.
Any other model or effort requires the maintainer's explicit approval.
Before handoff, assess the full
expected change—including behavior, supporting changes, tests, and new
concepts—against the quick maintainer review target in
[Work scope and sizing](workflow.md#scope-and-sizing). If it is too large, split
it into independently reviewable nested Works first. For an ad hoc handoff,
define a parent Work and child Works; for an existing Work, nest children and
update its parent map. Review and merge the revised plan before expanded work
begins. Preserve the explicit maintainer scope exception; plan approval alone
does not waive the review target.

Before dispatch, identify dependencies and shared edit surfaces. Coordinate
shared owners, parent maps, indexes, exact wording, formatter-valid snippets,
and reserved WDR numbers where needed. If overlap is unavoidable, sequence the
Works or name the remaining merge resolution; do not invent index categories or
ordering to hide a conflict. Start the executor promptly once necessary
preflight is complete; remaining reviewer reading may overlap execution when
it does not defer integration preflight.

A Work README and its linked contracts define acceptance criteria. Give
the executor the Work path and requested action, plus only missing steering and
necessary branch or delivery context. The executor reads the Work and applicable
contracts; consult ancestor READMEs only as needed, without recursively loading
every parent. Without a Work contract, state acceptance criteria in
the handoff. Link background instead of forwarding the full conversation by
default. Routine choices within the agreed contract need no approval.

Every leaf executor creates and uses an isolated Git worktree before editing.
Before work begins, the handoff names the destination path and branch and gives
the command, for example:

```sh
make worktree-create WORKTREE=/private/tmp/ataraxia-example BRANCH=work/example
```

If implementation reveals out-of-scope work, stop before expanding and report
the finding and evidence. Apply the split rule when it adds an independent
responsibility or exceeds the review target. A different delegated agent still
requires the maintainer's explicit approval.

## Review and return

After handoff and each correction request, wait for the completed artifact or a
blocker needing maintainer steering before reviewing. Do not poll for routine
status, inspect partial diffs, or send
fragmented corrections. Review the completed diff once against acceptance and
owner guidance, using reported evidence. Send one consolidated finding list to
the same executor session; review corrections as needed. Reuse reported evidence
and rerun focused checks only when a change, failure, or unresolved concern
warrants it. Context reuse may help token caching, but caching is not
guaranteed. If the same finding remains after a correction attempt, or the
session cannot continue, stop and report attempts, current evidence, and the
specific decision or help needed. Resume only with orchestrator or maintainer
steering. If the executor is unavailable, report that and wait; do not silently
switch agents or implement its changes as a fallback. Keep independent review
and maintainer review, merge, and CI gates.

Before removing a completing Work's contract, independently review its
criterion statuses and evidence using the
[Work delivery commit procedure](acceptance-tracing.md#work-delivery-commits).

If an executor session is cancelled or lost, recover from the Work contract,
parent map, branch or PR, and available evidence. Establish which changes
remain, which evidence applies to the current revision, and which criteria are
unresolved before continuing. If uncertain, state that and ask for steering
rather than treating the handoff as complete. A fresh executor session may
continue the same scope after recovery.

Follow [acceptance tracing](acceptance-tracing.md) for criterion status,
coverage semantics, evidence methods, and the retained verification/cleanup
commits. Follow
[Pull requests](pull-requests.md#descriptions) for executor returns, local
review before new or amended PR publication, description preparation, ready-PR
meaning, and publication ownership.

Before publishing, reassess maintainer review effort from the actual diff,
including tests, supporting changes, and concepts. If it exceeds the target,
stop publication and partition the completed work into at least two cohesive,
independently reviewable child Work PRs within the target. Define their
contracts and dependencies, update the parent map, and get the revised parent
plan reviewed and merged before child delivery continues. Preserve and reuse
completed implementation and valid evidence, identify remaining merge
resolution, and reassess each child diff before publication. The explicit
maintainer scope exception in
[Work scope and sizing](workflow.md#scope-and-sizing) still applies.

Repository merge settings do not replace maintainer review or maintainer
authority. The maintainer reviews the current PR revision and performs the
merge. Agents must not merge autonomously; an agent may merge only with explicit
maintainer instruction. Do not change repository settings, use an admin
override, or bypass review or CI requirements.

Return the reviewable artifact (branch and revision or PR), outcome, acceptance
evidence, commands run, unrun checks, unresolved criteria, and blockers. After
session recovery, include the recovered state.
A blocked return states what remains and what input or decision is needed. A
completed return identifies changes awaiting orchestrator review.
