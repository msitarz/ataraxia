# Orchestrator handoffs

Read when acting as orchestrator for repository changes.

## Roles and delegation

The orchestrator owns scope, planning, read-only investigation, and independent
review and verification. Luna makes the bounded changes and returns the
artifact and evidence; it works directly within scope and does not recursively
delegate the same task.

Delegate repository changes to Luna at low reasoning effort. Higher effort
requires the maintainer's explicit approval. Before handoff, assess the full
expected change—including behavior, supporting changes, tests, and new
concepts—against the quick human-review target in
[Work scope and sizing](workflow.md#scope-and-sizing). If it is too large, split
it into independently reviewable nested Works first. For an ad hoc handoff,
define a parent Work and child Works; for an existing Work, nest children and
update its parent map. Review and merge the revised plan before expanded work
begins. Preserve the explicit maintainer scope exception; plan approval alone
does not waive the review target.

A Work README and its linked contracts define acceptance and completion. Give
Luna the Work path and requested action, plus only missing steering and
necessary branch or delivery context. Luna reads the Work and applicable
contracts; consult ancestor READMEs only as needed, without recursively loading
every parent. Without a Work contract, state acceptance and exit criteria in
the handoff. Link background instead of forwarding the full conversation by
default. Routine choices within the agreed contract need no approval.

If implementation reveals out-of-scope work, stop before expanding and report
the finding and evidence. Apply the split rule when it adds an independent
responsibility or exceeds the review target. A different delegated agent still
requires the maintainer's explicit approval.

## Review and return

After handoff, wait for the completed artifact or a blocker needing maintainer
steering. Do not poll for routine status, inspect partial diffs, or send
fragmented corrections. Review the completed diff once against acceptance and
owner guidance, using reported evidence. Send one consolidated finding list
to the same Luna session; review corrections as needed. Reuse reported checks
and rerun focused checks only when a change, failure, or unresolved concern
warrants it. Wait for the corrected completed result or a blocker before
reviewing again. Context reuse may help token caching, but caching is not
guaranteed. If the same finding remains after a correction attempt, or the
session cannot continue, stop and report attempts, current evidence, and the
specific decision or help needed. Resume only with orchestrator or maintainer
steering. If Luna is unavailable, report that and wait; do not silently switch
agents or implement its changes as a fallback. Keep independent review and
human review, merge, and CI gates.

If a Luna session is cancelled or lost, recover from the Work contract, parent
map, branch or PR, and available check results. Establish which changes remain,
which evidence applies to the current revision, and which criteria are
unresolved before continuing. If uncertain,
state that and ask for steering rather than treating the handoff as complete.
A fresh Luna session may continue the same scope after recovery and must return
the recovered state and evidence.

The orchestrator may review the branch directly or create a draft PR when Luna
completes the handoff. Draft means changes are complete and await orchestrator
review. Once independent review and any correction loop pass, mark the PR ready.
Ready means agent review passed and maintainer review is requested; it does not
mean maintainer approval, merge, or successful CI. The maintainer retains final
review and merge decisions. Before marking ready, reassess human review effort
from the actual diff, including tests, supporting changes, and concepts. If it
exceeds the target, stop and revise the split plan, then get the revised parent
plan reviewed and merged before child work continues. An explicit maintainer
request may authorize a larger review under
[Work scope and sizing](workflow.md#scope-and-sizing).

Return the reviewable artifact (branch and revision or PR), outcome, acceptance
evidence, checks and results, unrun checks, unresolved criteria, and blockers.
Use the Work contract's evidence method; see
[acceptance tracing](acceptance-tracing.md) for criterion status and coverage
semantics. A blocked return states what remains and what input or decision is
needed. A completed return identifies changes awaiting orchestrator review.
