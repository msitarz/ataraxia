# Install the locked Mermaid backend

Use normal locked uv setup on supported CI and Intel macOS. Worktree creation
and its fresh-worktree CI verification belong to the
[next leaf](../worktree/README.md).

Own development-only Mermaid dependencies and the lock, setup documentation,
and a reusable smoke test through our setup boundary. Pin mermaidx 0.9.5 and
QuickJS-ng 0.17.0.1. Intel macOS x86_64 uses the published QuickJS-ng wheel
through a `tool.uv.sources` platform marker; all other platforms use the PyPI
release. The Intel wheel's SHA-256 is
`39f9634bbec364470982342d7a7ae729dd4b635a652c6300e31e281e7d7e199e`.
Do not add a source checkout, custom build path, platform allowlist, Python
minor cap, or architecture switch. Keep the dependencies in the dev group, not
the trading package.

`make ci-test` performs ordinary locked setup, checks the prepared environment
offline, then runs tests. The following worktree leaf may reuse that environment
and the existing real forced-QuickJS rendering smoke test. Do not change CI jobs
or introduce an alternate installer.

- **AC-1 DONE** Given a clean Intel macOS x86_64 checkout and the Linux CI
  checkout, ordinary locked uv setup installs mermaidx 0.9.5 and QuickJS-ng
  0.17.0.1 from the platform-appropriate source, and the prepared QuickJS
  backend renders SVG without a manual build or temporary wheel.

  Validation: independently review the fresh Intel macOS setup and exact-head
  Linux Actions install/render evidence. Confirm source selection, wheel hash,
  resolved versions, and that no QuickJS build or bootstrap ran; run the Work's
  selected smoke test.
- **AC-2 DONE** Given the prepared environments, offline setup verification
  and the forced QuickJS rendering smoke test succeed on Intel macOS and Linux.

  Validation: independently inspect Intel macOS `make verify-setup` and smoke
  output plus the exact-head Linux `make verify-setup` and smoke output. Confirm
  offline verification made no changes and did not resolve or download
  dependencies.

Follow [testing](../../../../testing.md),
[test ownership](../../../../test-ownership.md) and
[strict typing](../../../../engineering.md#preserve-type-precision).
