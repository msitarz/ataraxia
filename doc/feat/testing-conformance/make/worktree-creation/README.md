# Worktree creation

Depends on stub helper. Extract creation cases into a focused typed module. Keep
real disposable Git and cache copying, a fixture-file setup fake, explicit Git
configuration, and process timeouts. Preserve destination-local paths, literal
hostile names, missing/partial cache, verification failure, and conflicts.

- **AC-1 TODO** Given successful or refused creation, destination
  caches/environment and Git registrations match the contract; setup failures
  retain recoverable worktrees and conflicts preserve existing files/refs.

  Validation: run focused marked creation cases and strict typecheck; review
  before/after state, absence of execution markers, retained provenance, and
  full CI.
