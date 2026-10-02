# Documentation fixture Work

This standalone, bounded task is the trial fixture. From the repository root,
use this Work, [facts.md](facts.md), and [guide.md](guide.md). Rewrite
`guide.md` with exactly these headings, in order: **Preconditions**, **Steps**,
and **Limits**. Preserve every source fact and link, remove repeated
information, and add no rules. Only `guide.md` may change.

In a fresh workspace, run `make help` and `make setup`, then
`make doc-format ARGS=doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/single-agent-execution/protocol-and-fixture/fixture/guide.md`
and `make doc-check`. Return the artifact, corrections, and check outcomes.

## Acceptance checks

- The three required headings appear in order, and all source facts are
  accurately presented without repetition.
- The original local link remains valid; no rule is invented; no file except
  `guide.md` changes.
- Formatting and local-link checks pass.
