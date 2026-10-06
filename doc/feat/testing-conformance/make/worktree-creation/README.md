# Worktree creation

Split typed repository/setup support from creation-case migration to keep each
complete diff within the
[five-minute review target](../../../../workflow.md#scope-and-sizing). Keep real
disposable Git and cache copying; fake only external dependency setup.

- **DONE** Typed isolated Git/setup helper and real-Make creation smoke.
- **TODO** [Creation cases](cases/README.md).

Merge this revised map before delivery. Cases follow the delivered helper;
sequence shared
support, Pyrefly inclusion, and parent-map edits. Reuse delivered Make support
narrowly; no generic fixture framework, production changes, or unrelated
cleanup.

- **AC-1 TODO** Given successful or refused creation, destination
  caches/environment and Git registrations match the contract; setup failures
  retain recoverable worktrees and conflicts preserve existing files/refs.

  Validation: run focused marked creation cases and strict typecheck; review
  before/after state, absence of execution markers, retained provenance, and
  full CI.
