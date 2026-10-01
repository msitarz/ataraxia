# Orchestrator handoffs

Read when acting as orchestrator for repository implementation.

## Roles and delegation

The orchestrator owns scope, planning, read-only investigation, and independent
review and verification. Luna is the implementation agent: it implements the
bounded handoff and returns changes and evidence. It works directly within its
scope and does not recursively delegate the same task.

Delegate repository implementation to Luna at low reasoning effort. Higher
reasoning effort needs the maintainer's explicit approval. Split work that is
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
not guaranteed. If Luna is unavailable, report it to the maintainer and wait
for direction; do not silently switch agents or implement the handoff as a
fallback. Agent review does not replace the maintainer's manual review and
merge decision.
