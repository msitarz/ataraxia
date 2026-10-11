# Verify fresh offline worktrees through CI

Depend on the accepted locked backend setup outcome in the
[setup delivery map](../README.md#delivery-map).
Consume its prepared uv download cache/environment and reusable
`test/script/integration/test_mermaid_backend.py` smoke test.
The review question is whether a fresh worktree of the reviewed revision can
prepare and render offline through a bounded existing CI route. Do not change
dependencies or backend selection. This remains future work; no worktree CI
implementation is part of the current backend simplification.

`worktree-create` already creates a branch worktree from `master`, copies
`.cache`, installs locked dependencies offline into a fresh `.venv`, and runs
`verify-setup` before reporting readiness. Existing
[creation tests](../../../../../test/make/integration/test_worktree_creation.py)
cover cache/environment routing, failed preparation and refusal preservation;
they use a setup double and do not prove real renderer availability there.
The existing backend smoke test already forces SVG rendering with a 30-second
deadline. Reuse these owners rather than repeat setup or renderer logic.

Deliver `make verify-mermaid-worktree` as a small composition: select the
reviewed revision explicitly, call `worktree-create`, then run only the existing
backend smoke test there offline/no-sync. Add optional `BASE` to
`worktree-create` for this missing revision selection, retaining default
`master` and ordinary refusal/recovery behavior. Do not run a second
`verify-setup` after creation. Actions may check out a PR merge revision;
identify the actual checked-out commit and its relation to the reviewed PR head
so older `master` or another head cannot supply the evidence.

Clean up only the route's newly created disposable worktree and branch on
success or failure; leave caller-owned files, refs and worktrees intact.
Preserve the original failure and report cleanup failure. Bound external
execution and reap timed-out children using ordinary subprocess facilities; a
process framework or generalized worktree lifecycle is outside this outcome.

Append this route after ordinary backend validation in existing `ci-test`;
do not create a new CI job or run setup/network downloads during verification.
Coordinate shared Make/test helpers and setup docs after backend delivery.
Use the parent's required Intel macOS/Linux verification scope and the
[authorized publication/evidence sequence](../README.md#required-evidence-sequence).

- **AC-1 DONE** Given the prepared Intel macOS environment, the real
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
- **AC-3 DONE** Given the new route succeeds, fails or times out, its disposable
  artifacts are removed, the failure remains visible, and caller state is
  preserved. Explicit revision selection works while ordinary creation still
  defaults to `master` and retains its refusal/recovery behavior.

  Validation: extend existing disposable Make/Git helpers and creation tests
  only for explicit revision selection and the new route's CI/offline routing,
  cleanup on success/preparation failure/render failure/timeout, and
  preservation of caller state. Reuse existing default/refusal/recovery tests
  without a new failure matrix for every creation stage. Doubles prove
  routing/failure effects only; real evidence above proves rendering. Run
  affected lint/type/doc/ac checks.

Follow [integration testing](../../../../testing-integration.md),
[testing](../../../../testing.md),
[test ownership](../../../../test-ownership.md) and
[strict typing](../../../../engineering.md#preserve-type-precision). Keep tests
at our worktree/Make boundary; add coverage references only for behavior the
reused tests actually establish. This leaf targets one five-minute review of
the missing proof route, including incremental tests and supporting docs.
