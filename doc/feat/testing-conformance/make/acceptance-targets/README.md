# Acceptance targets

Split nested pytest selection from static declaration validation so each
complete delivery fits the
[five-minute review target](../../../../workflow.md#scope-and-sizing).

- **TODO** [Work and criterion selection](selection/README.md).
- **TODO** [Declaration validation](declarations/README.md).

Merge this map before delivery. Selection precedes declarations; sequence
shared named fixtures, narrow disposable process support, Pyrefly inclusion,
and parent-map edits. Copy actual Makefile, acceptance scripts and required
dependencies/configuration; retain real-tool markers and original covers.
No checkout fixture writes, generic framework, production or tooling-policy
changes. Remove obsolete legacy support/module only when no callers remain.

- **AC-1 TODO** Given selection or declaration commands, real nested pytest
  selects the intended marked tests, unmatched criteria fail, and declaration
  checks never execute fixture tests or modify the original checkout.

  Validation: run focused marked acceptance-target cases and strict typecheck;
  review complete selection/failure observations and latest-head full CI.
