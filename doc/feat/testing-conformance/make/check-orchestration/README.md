# Check orchestration

Split preparation allocation from execution obligations so each complete diff
fits the [five-minute review target](../../../../workflow.md#scope-and-sizing).
Both children use the delivered typed Make sandbox without expanding its
fixture system or running real installs/network operations.

- **TODO** [Preparation allocation](preparation/README.md).
- **TODO** [Check execution](execution/README.md).

Merge this revised map before delivery. Preparation goes first, then execution;
sequence shared `test_makefile.py`, Pyrefly inclusion, and parent-map edits.
Preserve original covers markers and exact argument/environment contracts. Each
child owns a focused typed module; leave creation and unrelated tests alone.

- **AC-1 TODO** Given verify/CI/setup targets and injected failures, promised
  commands and flags are observed; stale setup stops later checks and audit
  failure reaches Make without performing installs or network operations.

  Validation: run focused criterion-marked cases and strict typecheck; review
  retained original covers markers, preparation obligations, and full CI.
