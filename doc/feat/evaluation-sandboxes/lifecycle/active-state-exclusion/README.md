# Per-sandbox active-state exclusion

Deliver the shared lifecycle marker and exclusive per-name OS-held lock,
including their integration into `sandbox-create`. Listing, removal and native
execution depend on this outcome and verify their own command integration. Reuse
[root and ownership resolution](../../README.md#shared-root-and-ownership).
There is no global registry, manual active bit, or controller service.

## Persistent private marker

At `1b31bba`, `script/sandbox.py` writes the root-private
`.<NAME>.ataraxia-sandbox.json` with canonical Git common directory, project,
base, preparation state and failure diagnostics. Extend this existing record
rather than add a second acceptance record. Keep it uncommitted and inaccessible
to child commands. Validated host-side updates preserve unrelated fields and
retain diagnostics; interrupted writes must never turn partial metadata into
valid ownership or approval.

Record a supported schema version, opaque unique sandbox generation, native
destination identity, owning Evaluation Work repository path, and owning
orchestrator identity. For each execution attempt record a unique run identity,
Codex session UUID when available, preparation/execution outcome (including
incomplete or unknown), and private output/artifact paths. A Codex session UUID
is distinct from a delegated agent identifier; add an agent identifier only if
needed for provenance. Never invent a missing UUID. Keep prior attempts and
artifacts when resuming or failing rather than overwrite their provenance.

Creation gains a required `EVALUATION_WORK=repository/relative/path` Make input
identifying the owning Evaluation Work with its README; reject absent, escaped
or unrelated paths before reservation. The orchestrator supplies host-side
owner provenance for creation and disposition. The shared host recording
interface accepts that owner, current identity/inventory bindings, retained
destinations, review reference and explicit retain/discard decisions; it returns
a validated persisted disposition or refuses without approval. Execution updates
only run/outcome/artifact fields and invalidation, never disposal approval.
Implementation may use a small shared helper and existing Make routing; no new
controller or external review service is required.

The owning orchestrator explicitly records cleanup disposition only after
artifacts are preserved and the maintainer has reviewed the cleanup decision.
It identifies that owner and review, the generation, current run/attempt and
session identity when known, exact workspace state (tip and changes), and exact
private output/artifact inventory or revisions, with retained destinations and
accepted import evidence or reviewed discard decisions where applicable.
Inactivity, clean status, a session ending, or executor-written claims cannot
supply this approval. Disposition is private host authority, not delegated to
the executor. Its host recording operation validates ownership and current
bindings under the same exclusive lock; it cannot race launch or deletion.
Do not require a new review system: reuse existing Work/PR review and artifact
preservation evidence. Removal consumes the validated disposition.

Clear disposition before any attempted new execution or resume, including one
that fails or is rejected after identifying the owned sandbox. A refused request
without enough trusted identity to update safely must leave the record untouched
and cannot confer approval. Any changed run, workspace, preparation state or
output invalidates the binding; missing/inconsistent bindings always refuse
removal. Failed preparation also requires explicit reviewed disposition covering
its partial workspace and diagnostics; no absence-of-work bypass is allowed.
There are currently no sandboxes requiring compatibility: reject old,
unsupported or malformed records safely without rewriting, migrating or deleting
them. Listing may report them as unsupported.

## Stable lock and exclusion

Use one regular private `.<NAME>.ataraxia-sandbox.lock` with an exclusive lock
held by the operating system. File existence and PIDs never establish liveness.
Creation initializes it atomically if absent only when no destination/marker
exists. Never unlink or replace it, including after successful deletion and
same-name reuse. Other operations fail closed on a missing, unsafe or symlinked
lock. Revalidate the open file against its path after acquisition to detect
replacement; child commands cannot access it.

Capture generation (or explicit absence for create) before waiting; after
acquisition reread it and revalidate destination identity. Abort if it changed.
Create reserves only a still-absent name, holds the lock through preparation and
durable ready/failed state, and retains failures without overwrite. Removal
holds the same lock from final safety/disposition checks through deletion, so
an inactivity check cannot race a new launch. Refusal releases without deletion.

`sandbox-exec` acquires automatically before launch and holds exclusion until
execution and all descendants capable of accessing the workspace/private output
are stopped and results retained. The orchestrator owns review and disposal,
not manual liveness unlocking. Implement OS lock lifetime and process handling
so a crashed wrapper cannot release exclusion while descendants still operate.
Do not let descendants escape the protected lifetime. If stopping or observing
all descendants cannot be established, retain an unknown execution marker and
refuse launch/removal until host-side recovery establishes stoppage and retains
results under the lock. OS release after process death alone does not establish
completed execution or disposability. No stale active bit needs manual clearing.

Listing opens existing safe locks only and performs an immediate nonblocking
probe, releasing on acquisition without writing, creating, replacing or
repairing anything. A busy lock reports active operation; a free lock reports
observed inactivity, separately from recorded outcome/disposition. Unsafe or
unavailable observations and generation changes report unknown. These are
momentary observations, never cleanup authority.

## Acceptance

- **AC-1 TODO** Shared exclusion and creation integration serialize same-name
  create/execution/removal, safely reserve missing names and retain ready/failed
  preparation markers with Evaluation ownership. Consumers need no manual lock
  commands; listing probes leave persistent state unchanged.

  Validation: criterion-marked subprocess tests cover create/create and shared
  create/execution, create/removal and execution/removal contention, readiness
  failure and reservation failure. Inspect creation metadata and private modes;
  each consumer Work verifies its command integration.
- **AC-2 TODO** Normal completion, interruption and crashes retain outcomes
  and artifacts; exclusion lasts through descendants and result retention.
  Unknown execution fails closed until safe recovery. Unsupported metadata,
  unsafe lock paths and stale identity cannot become authority.

  Validation: criterion-marked process fixtures terminate wrappers with live
  descendants and verify exclusion or unknown-state refusal until stoppage and
  preservation; cover interrupted marker updates and safe reacquisition. Review
  supported OS semantics, descendant lifetime and recovery. Test held/free/
  unobservable listing probes without persistent filesystem changes.
- **AC-3 TODO** Stable lock identity and fresh generation prevent old waiters
  from acting on same-name recreation. Failed preparation remains reserved;
  interrupted removal retains its marker and prevents unsafe name reuse.

  Validation: barrier-controlled fixtures capture generation A, remove A and
  create B before a waiting operation enters, then assert it aborts. Verify lock
  inode stability, fresh generation, retained failure identity and interrupted
  deletion behavior, with consumer integration in removal.
- **AC-4 TODO** Only the owning orchestrator can record a current explicit
  cleanup disposition after preservation and maintainer review. New, resumed,
  failed or rejected execution and changed output cannot reuse stale approval;
  failed preparation and unknown execution receive no automatic exemption.

  Validation: criterion-marked host-record fixtures exercise missing review,
  wrong owner, generation/run/output/workspace mismatch, changed artifacts,
  rejected/failed/resumed launch and failed preparation. Independently review
  existing evidence bindings and child/private trust boundary; no model run or
  speculative controller is required for this shared safety outcome.
