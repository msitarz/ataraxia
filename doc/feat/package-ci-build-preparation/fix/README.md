# Prepare the backend before offline wheel verification

Own the `ci-package-setup` preparation recipe in `Makefile` and package-specific
regressions in `test/make/integration/test_preparation.py`; use existing typed
real-Make/fake-uv support. Add an online wheel build after Python preparation,
such as `uv build --wheel --out-dir .cache/build`, before `verify-package`.
Retain that consumer's UV_OFFLINE/UV_NO_SYNC exports and the actual isolated
installed-wheel smoke in `script/smoke_installed_package.py` unchanged.

Update the affected package test/description and add focused failure cases.
Preserve markers and precisely type every changed test/helper, retaining their
normal strict includes; use concise slice docstrings. No blanket tool/hook/test
migration or shared helper redesign. Stop/report if supporting changes exceed
the complete-diff review target rather than expanding this fix.

- **AC-1 DONE** Given real Make with recorded fake uv, package CI requests
  Python preparation, then wheel/backend preparation, then smoke execution in
  that order. Preparation calls are online with no-sync retained; smoke is
  offline and no-sync. Python or build refusal prevents subsequent calls and
  propagates the exact Make failure outcome with distinctive diagnostics.

  Validation: add criterion-marked command/environment/order and failure
  regressions using existing disposable HOME/TMPDIR/cache arrangements. Run
  focused package cases and the preparation/execution modules, strict typing,
  lint/format and doc/ac checks. Fake uv proves routing, not actual preparation.
- **AC-2 DONE** Given a disposable empty UV_CACHE_DIR and prepared project
  tools, actual `make ci-package` prepares the backend online and completes real
  offline build/install/sample smoke verification. The same cold-cache flow
  succeeds with uv_build 0.12.23 in a disposable project copy, preserving
  tracked pins and the separate PR #172 unchanged.

  Validation: run real `make ci-package` with a newly created empty UV_CACHE_DIR
  for current pins; repeat with a separate empty cache and only the
  build-backend pin temporarily changed to 0.12.23 in a disposable copy. Keep
  the existing prepared tool environment available without relying on a warmed
  build cache. Inspect online preparation followed by offline smoke results and
  unchanged tracked dependencies; report network/setup gaps as unverified, not
  success. Require latest-head full CI; no tracked dependency update or PR
  mutation.
