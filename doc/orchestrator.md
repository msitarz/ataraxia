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

Check the changes against acceptance and owner guidance, then verify the
appropriate evidence. Send concrete findings to the same Luna session and
repeat until resolved. Reusing context may help token caching, but caching is
not guaranteed.

When Luna completes the handoff, the orchestrator may review the branch
directly or create a draft PR. Draft means the delegated changes are complete
and await orchestrator review. After the independent review and correction loop
pass, the orchestrator marks the PR ready for review. Ready means agent review
passed and maintainer review is requested; it does not imply maintainer approval
or merge, or successful CI. The maintainer retains the final review and merge
decision.

If Luna is unavailable, report it to the maintainer and wait for direction; do
not silently switch agents or make the delegated changes as a fallback.
