# Genuine provider resources under compute lifetime

After lifecycle units, own new `integration/test_compute_resources.py` and its
strict include, with precisely typed local Bar-consuming sinks/runners. Reuse
merged CSV arrangements and actual SourceNode/BarProvider/compute, retaining
ADR16 ownership. No patched cleanup or tracking-only resource substitute.

Separate full exhaustion, a runner raising after resource entry, and explicit
generator.close after first yield while another row remains. Capture actual
file handles and assert they closed after each path; preserve independent
complete Bars/results and exact propagated failure identity/reason. Distinguish
compute-generator closure from the Input tests' early source-context exit.
Do not depend on garbage collection, sleeps or context callback counts.

- **AC-1 DONE** Given real CSV-backed computation, exhaustion, runner error and
  explicit generator close each close the genuine provider resource and preserve
  literal values/errors at the caller under precise checked tests.

  Validation: inspect real handle state and ownership/closure timing; run
  resource integration and lifecycle units, plus the subtree's required checks.
