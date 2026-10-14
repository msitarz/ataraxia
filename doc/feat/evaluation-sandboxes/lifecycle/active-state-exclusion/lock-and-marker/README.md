# Stable lock and durable marker

Deliver safe named ownership and creation exclusion using the existing
`script/sandbox.py` record and root resolver described in the
[parent baseline](../README.md). Creation remains usable before later children
and requires no Evaluation binding or execution provenance. This child owns
shared identity, persistence, lock acquisition and observational probe APIs;
[execution recovery](../execution-recovery/README.md) and
[cleanup disposition](../cleanup-disposition/README.md) extend them serially.

## Marker and creation

Extend the existing root-private
`.<NAME>.ataraxia-sandbox.json` with canonical Git common directory, project,
base, preparation state and failure diagnostics, rather than add a second
acceptance record. Keep it uncommitted and inaccessible
to child commands. Validated host-side updates preserve unrelated fields and
retain diagnostics; interrupted writes must never turn partial metadata into
valid ownership or approval.

Creation records a supported schema version, opaque unique sandbox generation,
native destination identity and preparation state; execution provenance is
initially absent. Failed preparation retains its partial workspace/diagnostics
and reserved generation. Shared updates validate supported fields and preserve
unrelated fields, including later execution and disposition extensions.

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

Listing opens existing safe locks only and performs an immediate nonblocking
probe, releasing on acquisition without writing, creating, replacing or
repairing anything. A busy lock reports active operation; a free lock reports
observed inactivity, separately from recorded outcome/disposition. Unsafe or
unavailable observations and generation changes report unknown. These are
momentary observations, never cleanup authority.

The acquisition API takes root/name and a captured generation (or explicit
absence for create), and returns an exclusive scope with reread validated
marker/destination identity or refuses. The update API accepts that scope and a
validated record update, durably preserving existing fields. The probe API
returns active, observed inactive or unknown plus validated identity without
persistent mutation. Exact Python signatures are an implementation choice;
consumer commands use these APIs rather than duplicate path or identity checks.

Shared fixtures may model deletion/recreation under the lock; actual deletion,
marker-last cleanup and guarded retry remain owned by
[removal](../../removal/README.md). Retained markers reserve names even when a
partial directory is missing, so interrupted removal cannot enable reuse.

## Acceptance

- **AC-1 TODO** Shared exclusion and creation integration serialize same-name
  create/execution/removal, safely reserve missing names and retain ready/failed
  preparation markers without requiring execution provenance. Consumers need no
  manual lock commands; listing probes leave persistent state unchanged.

  Validation: criterion-marked subprocess tests cover create/create and shared
  create/execution, create/removal and execution/removal contention, readiness
  failure and reservation failure. Inspect creation metadata and private modes;
  each consumer Work verifies its command integration. Execution/removal
  fixtures acquire the real shared API, without delivering those commands.
- **AC-2 TODO** Interrupted marker updates, unsupported metadata, unsafe lock
  paths and stale identity cannot become authority. Held/free/unobservable
  listing probes preserve all persistent filesystem state and report generation
  changes as unknown.

  Validation: criterion-marked fixtures cover interrupted writes, safe
  reacquisition, unsupported/malformed records, missing/symlinked/unsafe locks,
  lock replacement after open and before validation, and unchanged persistent
  state through each probe. Independently review durable update semantics and
  the child/private boundary.
- **AC-3 TODO** Stable lock identity and fresh generation prevent old waiters
  from acting on same-name recreation. Failed preparation remains reserved;
  interrupted removal retains its marker and prevents unsafe name reuse.

  Validation: barrier-controlled fixtures capture generation A, model removal of
  A and create B before a waiting operation enters, then assert it aborts.
  Verify lock inode stability, fresh generation, retained failure identity and
  refusal of create with an interrupted-deletion marker, including absent
  partial directories; actual interrupted deletion integration belongs to
  removal.
