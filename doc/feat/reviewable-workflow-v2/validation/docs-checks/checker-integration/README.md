# Checker integration

Compose adopted Markdown hygiene and repository-specific semantic checks behind
`make doc-check`. Start with path identity, local links or tool-provided link
checks, and the recursive README contract. Let a path target affected rules and
no path run the full check. CI runs the complete deterministic gate.

Avoid custom code for checks an adopted tool already provides. Add rules in
small PRs when a concrete workflow invariant needs enforcement.
