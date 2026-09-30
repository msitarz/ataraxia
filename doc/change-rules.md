# Repair and scope rules

Read this file for any repository change.

## Fix the underlying problem

Optimize for the user's complete outcome and maintenance cost across code,
tooling, tests, and docs.

- Trace the cause before adding instructions, exceptions, duplication, or
  workarounds; fix it in the responsible component when possible. Existing
  behavior is evidence, not automatically the intended contract: resolve
  mismatches against the task and accepted decisions.
- Prefer one authoritative implementation or definition; other paths call,
  derive from, or link to it. Automate deterministic steps, such as running all
  required checks through `make ci` and validating invariants at their owning
  boundary.
- Make the smallest cohesive fix within scope. Preserve intentional differences
  and compatibility; avoid speculative abstractions and unrelated refactors.
  Explain any necessary workaround and its remaining limitation.
- **Revert fundamentally wrong approaches before reimplementing.** If your
  change violates an established contract or convention, revert it and
  compensating changes, including unnecessary supporting code and docs. Preserve
  unrelated work. Reimplement from the restored baseline using project
  conventions, then validate. Use a targeted fix for an isolated defect in an
  otherwise sound design.
- Update affected callers, tests, and docs together. Verify the actual command,
  API, or user flow, including failures. Do not weaken tests or documented
  expectations to accommodate defects, or leave the user compensating manually.
