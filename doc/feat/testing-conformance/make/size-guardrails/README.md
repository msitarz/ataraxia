# Size guardrails

Use named Python fixture files and disposable Make/config arrangements instead
of generated source inside the checkout. Retain real Ruff and real-tool markers;
type helpers/fixtures and preserve the 25/26/50/51 statement boundaries.

- **AC-1 DONE** Given the four statement-count fixtures, 25 is clean, 26 and 50
  are advisory successes, and 51 blocks lint through real Make/Ruff.

  Validation: run focused marked guardrail cases and strict typecheck;
  independently count fixture statements, inspect advisory/failure observations,
  and full CI.
