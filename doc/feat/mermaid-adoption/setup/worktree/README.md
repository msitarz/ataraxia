# Verify fresh offline worktrees through CI

Depend on accepted [backend setup/cache integrity](../backend/README.md).
Consume its prepared cache/environment and reusable real-render smoke test.
The review question is whether a fresh worktree of the reviewed revision can
prepare and render offline through a bounded existing CI route. Do not change
bootstrap, dependencies or backend selection.

Own `make verify-mermaid-worktree`, its existing CI test-route wiring and
worktree documentation/routing tests. Add optional `BASE` to `worktree-create`
only if needed, preserving the default `master` and existing refusal/recovery
behavior. The verification route selects the reviewed `HEAD` explicitly so
Actions cannot verify older `master` code. It creates a fresh disposable
worktree, reuses copied prepared caches, runs real offline setup/`verify-setup`
and the backend leaf's real render test with no-sync/offline settings. Bound
execution with explicit subprocess deadlines; fail on timeout or any failed
stage. Clean up disposable worktree/branch on success and failure without
removing caller-owned artifacts or hiding the failure. Preserve existing
`worktree-create` recovery semantics for ordinary callers.

Append this route after ordinary backend validation in existing `ci-test`;
do not create a new CI job or run setup/network downloads during verification.
Coordinate shared Make/test helpers and setup docs after backend delivery.
Retain current platform limits and the
[authorized publication/evidence sequence](../README.md#required-evidence-sequence).

- **AC-1 TODO** Given the prepared supported macOS environment, the real
  verification route creates a fresh worktree of the intended revision, prepares
  it offline from copied caches, passes `verify-setup` and renders SVG there.

  Validation: execute the actual route locally before publication and retain
  revision, versions, commands/results, offline settings and cleanup state.
  A cache/routing shim does not establish this outcome.
- **AC-2 TODO** Given accepted backend setup on Linux, Actions on the exact
  reviewed head run the same fresh-worktree offline verification successfully,
  including actual setup/environment check and rendering there.

  Validation: publish the independently reviewed implementation retaining this
  criterion `TODO`, then independently inspect exact-reviewed-head Actions
  route execution and actual backend evidence before acceptance/cleanup.
- **AC-3 TODO** Given routing inputs or a failed/stalled verification stage,
  default base compatibility, explicit reviewed-head selection, offline/no-sync
  execution, bounded failure propagation and disposable cleanup hold.

  Validation: criterion-marked Make integration tests in disposable repositories
  cover default/explicit base, CI routing, failure/timeout cleanup and caller
  state preservation. Typed process/tool doubles prove routing only; run real
  worktree evidence above plus affected lint/type/doc/ac checks.

Follow [integration testing](../../../../testing-integration.md),
[testing](../../../../testing.md),
[test ownership](../../../../test-ownership.md) and
[strict typing](../../../../engineering.md#preserve-type-precision). Keep tests
at our worktree/Make boundary and remap reused coverage to this owning contract.
