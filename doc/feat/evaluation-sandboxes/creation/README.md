# Create prepared sandboxes

Using the reconciled [preparation inputs](../preparation-input.md),
deliver
`make sandbox-create NAME=...` for trusted online preparation at a final
project-scoped temporary location. Freeze the selected committed base and
executor branch under existing contribution rules. Reuse native Git and Make
setup/hooks/readiness; `worktree-create` shares history and therefore cannot
provide the required independent shallow repository. Add only the owning Make
boundary and necessary preparation/ownership logic, without snapshot tooling,
cache reconstruction or a global registry.

Use the
[preserved native preparation input](../preparation-input.md#native-preparation-input)
to retain useful commands, checks and provenance through the ownership revision.

Own the shared implementation of the parent's
[root/ownership contract](../README.md#shared-root-and-ownership), reused by
list, remove and exec; preserve the launcher's TMPDIR while resolving the root.

## Acceptance

- **AC-1 DONE** A safe NAME creates one absent owned child beneath the managed
  root, bound to canonical source Git common directory, project and exact base.
  Unsafe names, traversal, symlinks,
  source/root destinations, unsuitable ownership/permissions and collisions
  fail before overwrite or escape, including dangling symlinks and changed
  selected input.

  Validation: criterion-marked Make-boundary tests reuse existing disposable
  repository/process helpers to verify resulting paths, ownership and unchanged
  rejected destinations; independently review necessary metadata and containment
  checks. Cover native temp selection, project-name derivation, SANDBOX_ROOT,
  unsafe fallback/roots, linked-worktree agreement and conflicting checkout
  refusal at our boundary. Do not create a new upstream fixture framework.
- **AC-2 DONE** Successful creation yields an independent depth-one selected
  clone with no origin/tags/alternates/hardlinked source objects or extra refs,
  fresh final-location environment/caches and installed pinned hooks through
  online `make setup`, followed by `make verify-setup`. Failed clone/setup/check
  retains owned partial state, diagnostics and failure status without readiness,
  automatic retry, overwrite or broader-access rescue.

  Validation: Make-boundary tests verify project routing, exact input and
  successful/failed artifacts using external-process doubles where appropriate;
  independent review checks native preparation against preserved evidence and
  actual setup declarations. Tests cover our orchestration and recovery, not
  upstream Git/uv behavior; restricted readiness belongs to enforcement.
