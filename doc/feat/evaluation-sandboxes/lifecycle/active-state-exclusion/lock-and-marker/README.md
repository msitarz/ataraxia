# Stable lock and durable marker

## Purpose

Prevent same-name lifecycle operations and interrupted metadata writes from
acting on an unowned or replaced sandbox.

## Goals

- Integrate stable per-name exclusion and durable identity into existing
  creation.
- Provide shared acquisition, update and observational probe APIs.
- Keep ready and failed preparation usable without execution provenance.

## Mechanisms

- `script/sandbox.py` supplies existing creation and shared root resolution.
- `.<NAME>.ataraxia-sandbox.json` is the existing root-private record extended
  with durable generation, destination and preparation identity.
- `.<NAME>.ataraxia-sandbox.lock` is the stable private object for exclusive
  OS-held coordination and observational probes.

## Acceptance criteria

### **AC-1 TODO** Serialize lifecycle operations and preserve preparation

Shared APIs serialize same-name operations and retain durable ready/failed
preparation.

- Create/create, create/execution, create/removal and execution/removal
  contention uses automatic exclusion without manual lock commands.
- Acquisition accepts root/name and a pre-wait generation or explicit create
  absence, returning exclusive scope only after rereading the marker and
  revalidating unchanged native destination identity.
- Creation reserves only a still-absent name, atomically initializes an absent
  regular private lock only without a marker/destination, and holds exclusion
  through durable ready/failed preparation.
- The marker records supported schema, opaque unique generation, native
  directory identity, canonical Git common directory, project, immutable base,
  preparation state and failure diagnostics.
- Creation needs no execution provenance, and failed preparation retains partial
  workspace, diagnostics and reserved generation without overwrite.
- Host updates use exclusive scope, validate supported fields, persist durably
  and preserve unrelated fields/diagnostics, including later
  execution/disposition extensions.
- The uncommitted marker stays inaccessible to children, and interrupted writes
  never confer ownership or approval through partial metadata.

Consumers use these APIs rather than duplicate identity checks; exact Python
signatures remain an implementation choice.

### **AC-2 TODO** Refuse unsafe authority and keep probes observational

Unsafe authority is refused, and lock probes leave persistent state unchanged.

- Existing-sandbox operations reject old/unsupported/malformed records and
  missing/unsafe/symlinked locks without rewriting, migrating or deleting them,
  preserving AC-1's absent-name creation exception.
- Acquisition revalidates the open lock against its path to detect replacement,
  and interrupted updates allow only safe reacquisition.
- Neither file existence nor PIDs establishes liveness, and private coordination
  state stays inaccessible to children.
- Probes open existing safe locks for immediate nonblocking acquisition,
  reporting busy as active, successful acquisition as momentary observed
  inactivity, and unsafe/unavailable observations or generation changes as
  unknown.
- Probes return validated identity/activity and release acquired locks
  immediately without substituting for recorded outcome, disposition or cleanup
  authority.
- Probes never write, create, replace, repair or migrate locks/markers, and may
  report unsupported records without compatibility migration.

No existing sandbox requires migration.

### **AC-3 TODO** Distinguish same-name generations

Stable lock identity and fresh generations prevent obsolete waiters from acting
on replacements.

- The lock is never unlinked or replaced, retaining its inode across successful
  removal and same-name recreation.
- An operation that captured generation A refuses if A is removed and B is
  created before acquisition.
- Failed-preparation and interrupted-removal markers reserve names even when
  partial directories are absent, so creation cannot overwrite them.
- [Removal](../../removal/README.md) holds shared exclusion through final
  safety/disposition checks and deletion, with no check/delete race or deletion
  on refusal.

Removal owns marker-last cleanup/retry; this Work supplies shared APIs and
creation integration, while consumers own their command integration.

## Dependencies

- **DONE** [Managed sandbox creation](../../../../../evaluation-sandboxes.md):
  supplies the existing private record, root resolver and preparation path.

## Links

- [Shared root and ownership](../../../README.md#shared-root-and-ownership):
  owns root selection and repository ownership consumed here.
