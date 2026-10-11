# Prepare reproducible Mermaid backend setup

Prepare the backend proposed by the [adoption plan](../README.md) through
ordinary locked uv setup and leave it usable offline, including fresh worktrees.
Backend setup is delivered; integrated setup acceptance remains open until the
worktree child is reviewed.

## Delivery map

- **DONE** Backend locked setup: Intel macOS uses the published QuickJS-ng wheel
  with its locked hash; other platforms use PyPI. Ordinary setup, offline
  verification and forced rendering passed on Intel macOS and exact-head Linux
  CI. See [setup instructions](../../../../CONTRIBUTING.md) and the reusable
  [backend smoke test](../../../../test/script/integration/test_mermaid_backend.py).
- **TODO** [Offline worktree CI validation](worktree/README.md): after backend
  acceptance, prove fresh offline worktree setup/rendering through existing CI.

```mermaid
flowchart LR
    Backend[Accepted locked backend setup] --> Worktree[Accepted offline worktree CI validation]
    Worktree --> Setup[Integrated setup acceptance]
    Setup --> Checker[Checker implementation unblocked]
```

The backend child is complete. Existing `worktree-create` already copies caches,
installs locked dependencies offline and runs `verify-setup`. The remaining
child composes that path with the existing forced-render smoke test, adds exact
revision selection, and owns its disposable cleanup and existing CI route. It
does not duplicate preparation or introduce a general lifecycle. The integrated
setup criteria below remain open until that child is independently accepted.

Intel macOS selects the
[public prebuilt QuickJS-ng wheel](https://github.com/msitarz/quickjs-ng/releases/download/v0.17.0.1-intel-macos/quickjs_ng-0.17.0.1-cp310-abi3-macosx_10_15_x86_64.whl)
through a platform marker in `tool.uv.sources`; other platforms use ordinary
PyPI resolution. The asset's expected SHA-256 is
`39f9634bbec364470982342d7a7ae729dd4b635a652c6300e31e281e7d7e199e`.
The integrated lockfile records that artifact/hash; custom source-build and
platform-allowlist machinery was removed in the accepted backend delivery.
No manual source build or temporary-wheel preparation is required; uv's ordinary
download cache feeds offline verification and worktree cache copying.

## Required evidence sequence

The worktree leaf is the remaining delivery. Publish its independently reviewed
implementation with its criteria `TODO`, then inspect setup, offline and
rendering evidence from Actions on that exact head. Keep missing or failed
evidence unresolved and retain the normal latest-head merge gate.

Required verification covers local macOS x86_64 and the existing Linux CI
architecture; it does not establish a supported-platform allowlist. Keep the
project's Python 3.14+ policy and normal tool compatibility without an exact
Python-minor cap or automatic architecture switch. Record actual OS,
architecture, Python and backend versions; untested targets have no claimed
evidence. Stop with evidence for failed required setup or expanded
responsibility and seek maintainer steering under the
[scope rules](../../../workflow.md#scope-and-sizing).

- **AC-1 TODO** Given clean disposable checkouts and project prerequisites on
  both required verification platforms, ordinary `make setup` locally and
  `make ci-setup` on Linux install the pinned backend without manual build or
  temporary-wheel steps, and force actual SVG rendering successfully.

  Validation: independently review accepted backend child evidence for real
  Intel macOS setup and exact-reviewed-head Linux Actions setup/rendering,
  including versions, provenance, licensing and reproducibility. Assess the
  integrated artifact; run doc/ac checks. Shims cannot establish platform proof.
- **AC-2 TODO** Given each prepared environment, offline `verify-setup` and
  forced SVG rendering succeed with no dependency resolution or download;
  worktree preparation remains usable from prepared uv caches.

  Validation: independently review ordinary offline setup/render evidence from
  backend and actual offline `worktree-create`/render evidence from worktree,
  for macOS and exact-reviewed-head Linux Actions. Assess their integrated
  interface; run focused integration tests where integration changes invalidate
  child evidence. Cache-routing tests alone do not prove offline operation.
- **AC-3 TODO** Given failed locked dependency setup, existing Make routes
  propagate failure and do not report readiness; uv dependency errors remain
  visible and actionable without silently replacing the backend or changing
  architecture.

  Validation: independently review existing Make failure propagation/readiness
  behavior, actual setup diagnostics and integrated dependency/setup docs.
  Retain focused repository-boundary regressions where needed; do not add tests
  of upstream uv dependency validation. Run doc/ac checks under
  the current [evidence policy](../../../validation.md).
