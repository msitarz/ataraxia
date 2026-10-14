# Per-sandbox active-state exclusion

Own the shared per-name claim mechanism and generation-revalidation contract.
This Work adds claim participation to `sandbox-create`; listing, removal, and
execution consume the protocol through their respective command Works.
Keep managed-root resolution and canonical repository-owner identity exactly
as defined by the existing
[root and ownership rules](../../README.md#shared-root-and-ownership). Extend
only each per-child owner record with the lifecycle generation ID and native
destination identity needed to distinguish and revalidate a sandbox instance;
do not add a global registry or redefine root/repository ownership. The
coordination state is private from child commands. This Work defines protocol
semantics, not a particular platform locking API.

## Identity and lock-object lifetime

The current root-private creation record `.<NAME>.ataraxia-sandbox.json`
contains source Git common directory, project, selected base, and preparation
state. Under the parent
[shared ownership contract](../../README.md#shared-root-and-ownership), it will
also contain an opaque unique generation ID and the platform-native identity of
the created child directory. These are per-child lifecycle identity fields;
root resolution and repository ownership continue to use the existing
canonical common-directory rules.

Use one regular, root-private lock object per `NAME`, at
`.<NAME>.ataraxia-sandbox.lock`. Create it atomically when first needed and
never unlink, replace, or treat it as an ownership record. Keep it across
successful removal and same-name recreation. It is coordination state, not a
registry; child discovery ignores it. Its stable identity ensures all
contenders for a name serialize across generations. A lock object without a
valid owner record does not establish that a sandbox exists.

Creation is the only command that initializes a missing lock object, and only
when no owner generation or destination exists. Other consumers fail closed if
the lock object is missing, not a regular file, or reached through a symlink.
After acquiring it, a claimant verifies that its open lock object still matches
the root-private per-name path; a replaced path invalidates the claim.

Every operation captures the current generation ID (or the explicit “no
generation” state) before waiting for the per-name claim. After acquiring the
claim, it rereads and compares the state before acting. Execution and removal
also verify the destination identity against the owner record. If the name now
identifies a different generation, the operation aborts without acting on it.
Creation may reserve only if it captured no generation and the name and
destination are still absent after claiming. This makes a waiter from an old
generation harmless after removal and recreation.

## Contract

- A claim is exclusive per `NAME` using the stable private lock object above.
  `sandbox-create` acquires it before reservation and holds it through durable
  generation/owner metadata, destination identity, and final ready or failed
  preparation state. Execution acquires it before invocation and holds it
  until the process stops and final status/output state is recorded. Removal
  acquires it before final safety checks and holds it through deletion.
- A second create, execution, removal, or conflicting operation cannot acquire
  while the claim is held. Acquisition is atomic. A caller that cannot establish
  the claim, verify the identity, or safely observe claim state fails closed
  before executing or deleting anything.
- Release on every normal exit. A process failure or crash must not leave a
  durable active bit that blocks recovery. A stale process identifier or
  child-written metadata does not prove that a claim is free.
  After a crash, the next operation may retry only after the OS-backed claim
  is verifiably available and it revalidates the same sandbox identity and
  reruns its own readiness or removal guards. Incomplete output remains subject
  to the separate [disposability proof](../disposability-proof/README.md).
- Removal must not replace or unlink coordination state while another contender
  could use it, and an old waiter must not act on a later sandbox that reuses
  the same name. A refused removal releases its claim and leaves workspace,
  private output, and diagnostics intact.
- Listing may make a transient nonblocking claim probe to observe whether the
  claim is held. If it acquires the claim, it releases it immediately and does
  no work under it; it never changes persistent coordination state. An unsafe,
  failed, or unavailable observation is reported as unknown, not inactive.

The parent [lifecycle map](../README.md) sequences this contract before create
adds claim participation and before listing, removal, and execution consume it.
The [removal outcome](../removal/README.md) also depends on the separate
disposability Investigation; that Investigation does not determine claim
mechanics.

## Acceptance

- **AC-1 TODO** `sandbox-create` uses one atomic, per-name exclusive claim;
  execution and removal consumers cannot enter while it is held, and listing
  can observe the claim without persistent mutation. Claims are released on
  normal completion, and refusal releases without changing protected data.

  Validation: criterion-marked tests cover create/create contention and the
  shared claim primitive's create/execution, create/removal, and
  execution/removal contention cases. Assert only one operation enters each
  contested interval; each consumer Work verifies its own command integration.
- **AC-2 TODO** Crash or unverifiable state fails closed without treating a
  stale PID or child-controlled metadata as authority. Once the OS claim is
  verifiably released, a retry revalidates sandbox identity and reruns the
  consumer's guards; incomplete output remains preserved. Listing uses a
  transient nonblocking probe, releases any claim immediately, and reports an
  unsafe or unavailable observation as unknown.

  Validation: criterion-marked subprocess tests terminate a claim holder,
  verify safe reacquisition and identity checks, and assert that incomplete
  output/diagnostics remain. Test listing probes for held, free, and
  unobservable claims; verify immediate release and unchanged persistent
  filesystem/metadata. Independently review lock-object lifetime and behavior
  if the platform cannot provide the required atomic claim.
- **AC-3 TODO** A stable private per-name lock object and opaque generation ID
  prevent old contenders from acting on a sandbox recreated under the same
  name. Successful removal deletes the owned child and generation metadata
  under the claim but retains the lock object, allowing later creation with a
  fresh ID. A failed preparation retains its partial state and generation ID;
  that name cannot be retried or overwritten until safely removed.

  Validation: inspect creation/removal metadata lifecycle and use a
  barrier-controlled process fixture: a waiter captures generation A, waits
  while the lock owner completes A's removal and B's creation, then aborts on
  B's different ID. Verify removal never unlinks/replaces the per-name lock
  object, and listing ignores it as a child.
