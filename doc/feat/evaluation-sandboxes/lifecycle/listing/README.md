# Read-only sandbox discovery

After [managed sandbox creation](../../../../evaluation-sandboxes.md), deliver
`make sandbox-list` using the shared
[root and ownership resolution](../../README.md#shared-root-and-ownership).
Its active/inactive classification observes the
[active-state exclusion contract](../active-state-exclusion/README.md)
with a transient nonblocking probe. If the probe acquires the claim, release it
immediately and do no work under it. Complete and merge that contract before
listing implementation. Capture the current generation ID (or absence) before
the probe, then re-read after it; if it changed, report the claim state as
unknown.
Inspect only direct children and the narrow per-child metadata already owned by
creation; do not add a registry or a second resolver. Report identity,
location, observed preparation/execution/failure state, and whether ownership
is valid, unknown, or invalid. This command is observational and does not
repair entries.

## Acceptance

- **AC-1 TODO** Listing reports owned ready, partial, failed, and active
  children, and classifies malformed, missing, or conflicting-owner metadata
  as invalid/unknown without trusting it. A missing managed root produces an
  empty result; an unsafe resolved root is reported as unsafe. Root agreement
  with creation is exact, including generation and destination identity; a
  different canonical Git common-directory owner is recognizable but not
  manageable.

  Validation: criterion-marked Make-boundary tests cover mixed child states,
  absent root, malformed/missing metadata, conflicting owner, and unsafe root;
  compare generation/destination identity against creation's metadata contract.
- **AC-2 TODO** Listing never follows child symlinks, persistently mutates files
  or metadata, or reads unrelated host data. Its nonblocking claim probe is
  released immediately if acquired; unavailable or unsafe observation is
  reported as unknown, including when generation identity changes around the
  probe. Symlinked children and metadata are reported as invalid entries rather
  than traversed or accepted as ownership evidence.

  Validation: criterion-marked tests include symlinked child, metadata symlink,
  malformed metadata, and held/free/unobservable claim probes. Assert targets
  are not read, the probe is immediately released, and persistent filesystem
  state is unchanged. Independently review metadata reads for scope.
