# Orchestrator handoffs

Read when acting as orchestrator for repository changes.

## Roles and delegation

The orchestrator owns scope, planning, read-only investigation, and independent
review and verification. Luna is the delegated agent: it makes the bounded
repository changes and returns the changes and evidence. It works directly
within its scope and does not recursively delegate the same task.

Delegate repository changes to Luna at low reasoning effort. Higher reasoning
effort needs the maintainer's explicit approval. Split work that is
too broad for a quick human review into nested Works first,
following [Work scope and sizing](workflow.md#scope-and-sizing).

Before handoff, assess the complete expected change, including behavior,
supporting changes, tests, and new concepts, against the target in
[Work scope and sizing](workflow.md#scope-and-sizing). If the expected review
is too large, define independently reviewable child Works and review the plan
before delegating.

For a Work, its README and linked contracts own acceptance and completion
criteria. Handoff with the Work path and requested action, adding only steering
or constraints absent from the contract plus necessary branch and delivery
context. Luna reads the Work and applicable linked contracts; read ancestor
Work READMEs only when needed, without recursively loading every parent. For
changes without a Work contract, state acceptance and exit criteria in the
handoff. Link to background instead of forwarding the full conversation by
default.

If new scope adds an independent responsibility or causes the complete expected
change to exceed the quick human-review target, stop adding that scope. For an
ad hoc handoff without a Work, define a parent Work and small reviewable child
Works; for an existing Work, nest children in its hierarchy and update the
parent map. Review and merge that plan before implementing the expanded child
scope. Routine choices within the agreed contract need no approval; preserve the
explicit maintainer scope exception in
[Work scope and sizing](workflow.md#scope-and-sizing).

## Review and return

Use the handoff guidance above, then wait for the completed artifact or a
blocker that needs maintainer steering. Do not poll for routine status, inspect
partial diffs, or send fragmented mid-task corrections.

Review the completed diff once against acceptance and owner guidance, using the
reported evidence. Send one consolidated finding list to the same Luna session
and review again after corrections only as needed. Reuse reported check
evidence; rerun focused checks when a change, failure, or unresolved concern
warrants it. Context reuse may help token caching, but caching is not
guaranteed. Keep independent review and human review, merge, and CI gates.

Before marking a PR ready, reassess the human review effort from the actual
diff, including tests, supporting changes, and concepts the reviewer must
understand. If it exceeds the target, stop and revise the split plan before
marking the PR ready, even when the agreed scope did not change. Follow the
stop-and-split rule above; get the revised parent plan reviewed and merged
before child work continues. An explicit maintainer request may authorize a
larger review under [Work scope and sizing](workflow.md#scope-and-sizing); plan
approval alone does not waive the target.

When Luna completes the handoff, the orchestrator may review the branch
directly or create a draft PR. Draft means the delegated changes are complete
and await orchestrator review. After the independent review and correction loop
pass, the orchestrator marks the PR ready for review. Ready means agent review
passed and maintainer review is requested; it does not imply maintainer approval
or merge, or successful CI. The maintainer retains the final review and merge
decision.

If Luna is unavailable, report it to the maintainer and wait for direction; do
not silently switch agents or make the delegated changes as a fallback.
