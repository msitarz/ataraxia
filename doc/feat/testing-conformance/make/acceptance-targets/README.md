# Acceptance targets

Copy actual Makefile, acceptance scripts, configuration, and named pytest
fixtures into a disposable checkout; do not create inputs in the live checkout.
Retain real-tool markers and typed timeout-owning helpers. Preserve
Work/criterion selection, no-match failure, declarations without test execution,
missing inputs, malformed criteria, and canonical Validation annotations.

- **AC-1 TODO** Given selection or declaration commands, real nested pytest
  selects the intended marked tests, unmatched criteria fail, and declaration
  checks never execute fixture tests or modify the original checkout.

  Validation: run focused marked acceptance-target cases and strict typecheck;
  review complete selection/failure observations and latest-head full CI.
