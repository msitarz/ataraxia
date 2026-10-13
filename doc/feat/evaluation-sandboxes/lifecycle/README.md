# Discover and safely remove sandboxes

After [creation](../creation/README.md), deliver `make sandbox-list` and
`make sandbox-remove NAME=...` through the shared
[root/ownership resolution](../README.md#shared-root-and-ownership), including
the optional SANDBOX_ROOT argument.
Discover direct children locally without a global registry. Listing is read
only; it reports each child's identity, location and observed preparation,
execution or failure state, distinguishing unknown or invalid ownership.

Listing and removal share one maintenance outcome and narrow ownership/state
boundary. Reassess the complete implementation and tests before dispatch and
publication; split through the parent planning gate if they exceed one short
review rather than expanding this leaf during execution.

## Acceptance

- **AC-1 TODO** Listing discovers owned ready, partial, failed and active
  children and identifies invalid/unowned entries without following symlinks,
  mutating state or reading unrelated host data. Missing root yields an empty
  result; unsafe root/metadata is reported rather than trusted.

  Validation: criterion-marked Make-boundary tests inspect listing and unchanged
  filesystem state for mixed children, missing root and malformed ownership;
  reuse creation's narrow metadata contract and existing Make helpers. Verify
  root agreement with creation and classification of a different canonical Git
  common-directory owner without permitting management of its children.
- **AC-2 TODO** Removal deletes only the named owned inactive disposable child.
  It refuses source/root/unowned/symlink/escaped paths, active execution, dirty
  files, meaningful committed work not delivered, or undelivered output. Failed
  preparation may be removed only when no meaningful work is lost. Refusal
  preserves workspace, private artifacts and diagnostics; no force bypass is
  introduced.

  Validation: criterion-marked Make-boundary tests verify successful removal and
  unchanged rejected trees, including committed-but-undelivered output and
  active-state races. Independently review the explicit accepted-delivery proof
  used to preserve meaningful work; a clean Git status alone is insufficient.
