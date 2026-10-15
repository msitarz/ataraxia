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

Shared acquisition serializes same-name create/create, create/execution,
create/removal and execution/removal operations without manual lock commands.
It accepts root/name and the generation captured before waiting, or explicit
absence for creation. After acquisition it rereads the marker and revalidates
native destination identity, refusing changes before returning an exclusive
validated scope. Consumers use this API rather than duplicate identity checks;
exact Python signatures remain an implementation choice.

Creation atomically initializes an absent regular private lock only when neither
marker nor destination exists, reserves only a still-absent name and holds
exclusion through preparation and durable ready/failed state. It records a
supported schema version, opaque unique generation, native directory identity,
canonical Git common directory, project, immutable base, preparation state and
failure diagnostics. Execution provenance is initially absent: creation remains
usable before later execution and disposition delivery. Failed preparation
retains partial workspace, diagnostics and reserved generation without
overwrite.

Host updates accept the exclusive scope, validate supported fields, persist
durably and preserve unrelated fields and diagnostics, including later
execution/disposition extensions. The marker remains uncommitted and
inaccessible to child commands. Interrupted writes never make partial metadata
valid ownership or approval.

### **AC-2 TODO** Refuse unsafe authority and keep probes observational

Existing-sandbox operations refuse old, unsupported or malformed records and
missing, unsafe or symlinked locks without rewriting, migrating or deleting
them; AC-1 owns absent-name creation. The open lock
is revalidated against its path after acquisition to detect replacement.
Neither file existence nor PIDs establish liveness. Interrupted updates allow
only safe reacquisition; private coordination state is inaccessible to children.

The shared probe opens only an existing safe lock and immediately attempts
nonblocking acquisition. Busy means active operation; successful acquisition
means momentary observed inactivity and is released immediately. Unsafe or
unavailable observations, including a generation change across the probe, mean
unknown. Probe results include validated identity but remain separate from
recorded outcome/disposition and confer no cleanup authority.

Probes preserve all persistent filesystem state: they never write, create,
replace, repair or migrate a lock or marker. Unsupported records may be reported
as unsupported. No existing sandbox requires compatibility migration.

### **AC-3 TODO** Distinguish same-name generations

The lock is never unlinked or replaced, including after successful removal and
same-name recreation. Its inode identity remains stable while each new sandbox
has a fresh generation. An operation that captured generation A refuses if A is
removed and B is created before it acquires the lock.

Retained failed-preparation and interrupted-removal markers reserve their names,
even when partial directories are absent. Creation cannot overwrite them.
[Removal](../../removal/README.md) holds this same exclusion from final safety
and disposition checks through deletion, releases refusals without deleting,
and owns marker-last cleanup and guarded retry; it cannot race a new launch
between inactivity checks and deletion. This Work supplies shared APIs and
creation integration, while each consumer owns its command integration.

## Dependencies

- **DONE** [Managed sandbox creation](../../../../../evaluation-sandboxes.md):
  supplies the existing private record, root resolver and preparation path.

## Links

- [Shared root and ownership](../../../README.md#shared-root-and-ownership):
  owns root selection and repository ownership consumed here.
