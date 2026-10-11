# Prepare the pinned backend and validate its cache

Deliver ordinary setup/offline rendering under the
[setup platform and evidence contract](../README.md). The review question is
whether supported setup prepares reproducible native inputs and refuses broken
caches instead of silently using them. Worktree creation and its dedicated CI
verification belong to the [next leaf](../worktree/README.md).

Own development-only dependencies/lock, setup/bootstrap tooling, its cache
validation and setup prerequisites/licensing in
[CONTRIBUTING.md](../../../../../CONTRIBUTING.md). Start with mermaidx 0.9.5,
Mermaid 11.16.0 and QuickJS-ng 0.17.0.1 from the immutable report linked by the
[adoption plan](../../README.md). Linux uses the normal pinned uv/PyPI route
with compatible published wheels first. macOS x86_64 uses an explicit complete
pinned source route where wheels are unavailable. Pins include wrapper/upstream
commits, submodules, permitted release-version adjustment, build backend and
compiler prerequisites. No manual build or disposable experiment wheel.

`make setup`, `make ci-setup` and dependency-lock preparation share one owned
bootstrap. Publish reusable inputs beneath the existing copied `.cache` tree;
ordinary prepared offline setup must validate/reuse them without fetching.
Validate cached revisions and allowed metadata changes, refusing wrong,
incomplete or modified inputs with actionable recovery instructions. Failed
staging must not appear ready. Bound bootstrap subprocesses with explicit
timeouts and preserve command/reason diagnostics on refusal or timeout. Never
switch architecture or backend automatically. Transitive licenses and source
provenance must be inspected; dependencies stay outside the trading package.

Own a reusable real-backend smoke test through our setup boundary that reports
the pinned engine and forces QuickJS SVG rendering, plus ordinary offline
`verify-setup` evidence. Run these in the existing CI test route, adding only
ordinary `verify-setup` routing if needed; the next leaf appends worktree
verification. Reuse the smoke test there. Do not implement the Markdown checker,
change `doc-check`, replace CI jobs or adopt a browser/Node toolchain.

- **AC-1 TODO** Given a clean macOS x86_64 checkout and declared prerequisites,
  ordinary `make setup` installs the pinned backend reproducibly and the real
  smoke test forces SVG rendering without manual build/temporary-wheel steps.

  Validation: execute locally before publication; retain actual versions,
  source/build provenance, commands/results and license inspection.
  Independently review bootstrap/dependency scope and setup documentation.
- **AC-2 TODO** Given a clean supported Linux CI checkout, normal pinned
  uv/PyPI setup installs compatible wheels through `make ci-setup`, and the
  real smoke test reports the pinned engine and renders SVG successfully.

  Validation: publish the independently reviewed implementation with this
  criterion `TODO`, then inspect actual exact-reviewed-head Actions setup and
  criterion-marked real rendering evidence. Record resolved versions/route;
  stop for maintainer steering if the normal Linux route fails.
- **AC-3 TODO** Given each platform's prepared environment, offline
  `verify-setup` and real rendering succeed without download or resolution.

  Validation: run with network unavailable after setup locally on macOS, then
  inspect exact-reviewed-head Linux Actions offline/no-sync execution. Retain
  results and marked smoke-test execution; routing shims are insufficient.
- **AC-4 TODO** Given unsupported platform/Python, missing tools/sources,
  corrupted cached inputs or stalled preparation, setup refuses with contextual
  diagnostics and bounded execution, leaves failed staging unready, and never
  silently repairs, substitutes or changes architecture.

  Validation: focused criterion-marked tests through the owned bootstrap/setup
  boundary cover supported routing, refusal, missing offline inputs, timeout
  and tracked-source/metadata corruption. Inspect cleanup/cache invariants and
  typed boundary handling; run affected lint/type/doc/ac checks.

Follow [testing](../../../../testing.md),
[test ownership](../../../../test-ownership.md) and
[strict typing](../../../../engineering.md#preserve-type-precision). Retain our
cache/setup regressions; distinguish one-time upstream probes. Map reused tests
to this owning contract and retain only still-applicable observed evidence.
