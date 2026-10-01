# Orchestrator handoffs

Read when acting as orchestrator for repository changes.

## Roles and delegation

The orchestrator owns scope, planning, read-only investigation, and independent
review and verification. Luna is the delegated agent: it makes the bounded
repository changes and returns the changes and evidence. It works directly
within its scope and does not recursively delegate the same task.

Delegate repository changes to Luna at low reasoning effort. Higher reasoning
effort needs the maintainer's explicit approval. Split work that is
too broad for a quick review of one responsibility into nested Works first,
following [Work scope and sizing](workflow.md#scope-and-sizing).

Give Luna only the context needed: outcome, scope, acceptance criteria,
exclusions, relevant decisions and constraints, baseline or branch relationship,
links to applicable Work and owner guidance, and evidence to return. Link to
background instead of forwarding the full conversation by default.

## Review and return

Give Luna one focused handoff with acceptance and exit criteria, then wait for
the completed artifact or a blocker that needs maintainer steering. Do not poll
for routine status, inspect partial diffs, or send fragmented mid-task
corrections.

Review the completed diff once against acceptance and owner guidance, using the
reported evidence. Send one consolidated finding list to the same Luna session
and review again after corrections only as needed. Reuse reported check
evidence; rerun focused checks when a change, failure, or unresolved concern
warrants it. Context reuse may help token caching, but caching is not
guaranteed. Keep independent review and human review, merge, and CI gates.

When Luna completes the handoff, the orchestrator may review the branch
directly or create a draft PR. Draft means the delegated changes are complete
and await orchestrator review. After the independent review and correction loop
pass, the orchestrator marks the PR ready for review. Ready means agent review
passed and maintainer review is requested; it does not imply maintainer approval
or merge, or successful CI. The maintainer retains the final review and merge
decision.

If Luna is unavailable, report it to the maintainer and wait for direction; do
not silently switch agents or make the delegated changes as a fallback.
