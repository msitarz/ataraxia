# Prepare reproducible Mermaid backend setup

Deliver one supported installation path for the backend proposed by the
[adoption plan](../README.md), before implementing its checker. The review
question is whether ordinary repository setup can prepare the pinned backend
on both required platforms and leave it usable offline.

Scope includes development-only dependency and lock configuration, the existing
Make setup owners, necessary bootstrap tooling/tests, and prerequisites in
[CONTRIBUTING.md](../../../../CONTRIBUTING.md). Do not add a checker, change
`doc-check`, replace CI jobs or adopt a browser/Node toolchain. Reuse existing
setup and CI entry points rather than a second manual installation procedure.

Start with mermaidx 0.9.5, Mermaid 11.16.0 and QuickJS-ng 0.17.0.1 as evidenced
in the [parent report](../README.md). Resolve complete pinned sources and build
requirements if source compilation is needed: wrapper/upstream commits,
submodules, release-version adjustment, build-backend pin, compiler and OS
prerequisites must be explicit and reproducible. A temporary experiment wheel,
an untracked manual build or trusting a universal2 tag is insufficient. Keep
backend dependencies out of the installed trading package. Inspect transitive
licenses and record limitations at their authoritative setup owner.

Support is bounded to Python 3.14/local macOS x86_64 and existing Linux CI
architecture. Do not infer arm64 support from a wheel tag or run under a changed
architecture without authorization. Stop with evidence if required setup fails,
needs upstream implementation changes, or adds independent source-distribution
responsibility; seek maintainer steering and split the Work when required by
[scope rules](../../../workflow.md#scope-and-sizing).

- **AC-1 TODO** Given clean disposable checkouts and declared native
  prerequisites on both required platforms, ordinary `make setup` locally and
  `make ci-setup` on Linux install the pinned backend without manual build or
  temporary-wheel steps, and force actual SVG rendering successfully.

  Validation: execute these real setup routes on each platform and retain
  versions, source provenance, commands and results in delivery evidence.
  Inspect dependency scope, licenses and reproducibility; report missing
  platform execution as unresolved rather than accepting a shim as proof.
- **AC-2 TODO** Given each prepared environment, offline `verify-setup` and
  forced SVG rendering succeed with no dependency resolution or download;
  supported worktree preparation remains usable from prepared caches.

  Validation: execute with network access unavailable after setup on each
  target, including the existing `worktree-create` preparation path. Retain
  actual results; cache-routing tests alone do not prove offline operation.
- **AC-3 TODO** Given absent prerequisites, unavailable sources or an
  unsupported architecture, setup fails with actionable setup diagnostics
  without changing architecture, silently replacing the backend or claiming
  readiness.

  Validation: focused criterion-marked tests through the owned setup boundary
  cover refusal/error propagation; independently review prerequisite and
  platform documentation. Run affected lint, type, doc and ac checks following
  current [testing](../../../testing.md) and
  [evidence policy](../../../validation.md).
