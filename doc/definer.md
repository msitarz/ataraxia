# Definer guidance

Read when assigned to define or change a Work contract as a Definer.

The Definer owns the assigned Work contract changes and serial coordination of
shared parent-map edits. Do not implement the Work or approve your own
definitions, and do not recursively delegate the assigned task. The
owning Orchestrator retains scope and scheduling decisions, coordination beyond
the assigned contract and map edits, independent review, and maintainer handoff.

Read the assigned Work README and applicable linked contracts when provided. If
the handoff has no Work contract, use its acceptance criteria. Consult ancestor
Work READMEs only as needed. Use an isolated Git worktree before editing and
follow the assignment's create or resume instructions. Verify that the supplied
worktree, branch, and base match the assignment and that its environment is
ready; follow the
[contributor setup guidance](../CONTRIBUTING.md#getting-started). Work contract
structure and authoring instructions belong to the
[Work contract template](work-contract-template.md);
[Work definition](work-definition.md) provides contract context and specialized
Work requirements. Follow the
[routine-choice rule](workflow.md#scope-and-sizing) for choices within the
approved scope. Apply the repository's
[repair and scope rules](change-rules.md#fix-the-underlying-problem).

If the assignment or acceptance criteria are missing or inconsistent, or the
required work exceeds the approved scope, stop before expanding and report the
finding and evidence to the owning Orchestrator. Route a needed split or
maintainer decision through the
[Work pause rules](workflow.md#decisions-and-new-splits); the Orchestrator
coordinates the requested-tree pause and steering. Address a correction request
within the approved scope and return the revised contract and evidence. If the
same finding remains after a correction attempt or you cannot continue, stop
and report the attempts, current evidence, and specific steering needed. When
the owning Orchestrator resumes work after an interruption, reconstruct the
changes from the contract, parent map, branch or PR, and available evidence.
Report which changes remain, which evidence applies to the current revision,
and which criteria are unresolved. If the state is uncertain, report that and
wait for Orchestrator steering. Session selection and recovery decisions remain
with the owning Orchestrator.

Return the contract revision, outcome, dependencies, material risks, unresolved
criteria, and blockers to the owning Orchestrator. Point to existing evidence
sources needed for review under
[Work acceptance](acceptance-tracing.md#evidence). After recovery, identify the
recovered state and evidence that applies to the current revision. A blocked
return says what remains and what input or decision is needed; a completed
return identifies changes awaiting independent Orchestrator review.
