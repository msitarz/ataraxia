# Artifact delivery Investigation

How should the orchestrator turn isolated shallow-clone artifacts into reviewed
commits and a PR: import commits into its full-history repository, transfer
patches, or publish directly from the clone after review?

Follow the [parent's execution gate](../README.md#execution-gate-and-limits).
Use demonstrated outcomes from
[Sandbox isolation](../sandbox-isolation/README.md) and
[Executor communication](../executor-communication/README.md) for one integrated
artifact-to-publication demonstration. Deterministic Git candidate probes may
use independent disposable fixtures before those outcomes are ready.

If isolation or communication is infeasible, retain the dependency evidence and
complete deterministic transport probes independently. Report the integrated
demonstration as blocked and recommend against adoption or identify further
Work; a negative feasibility result can complete this Investigation.

## Candidates and trials

Prepare a full-history source and bare publication remote with the selected
base. A restricted executor generates changes and commits in its shallow clone;
it has neither source read access nor publication credentials. Include text,
binary content, a deletion or rename, and an executable-bit change in a small
fixture. Exercise actual staging and commits with hooks and protected Git paths;
if denied, test orchestrator-created commits from returned files separately.

Compare through real Git commands:

- Fetch the executor's assigned branch into the full-history orchestrator
  repository. Verify existing ancestry completes the history without making
  the receiver shallow or importing unrelated refs.
- Transfer a `format-patch`/`am` series including binary changes. Distinguish
  preserved authorship and order from rewritten IDs. Evaluate raw diff fallback
  only with explicit metadata and separate commit reconstruction.
- Have the orchestrator review and push directly from the clone outside the
  executor's restricted command policy. Test both a receiver with the base
  ancestry and one missing it; do not enable shallow updates to hide missing
  history. Main-checkout import is a candidate, not inherently required.

Preserve the verified implementation/evidence commit followed by separate
cleanup under
[acceptance tracing](../../../../../../acceptance-tracing.md#work-delivery-commits).
Independently review fixture criteria before marking them complete and removing
their contract; exercise the correction loop and refresh invalidated evidence.
Compare commit IDs where direct transfer preserves them, and compare trees,
metadata, and ordered changes when reconstruction rewrites IDs.

Advance the upstream base and test one clean rebase and one conflict. Keep the
executor history-excluded during reconciliation: full-history work belongs to
the orchestrator, or newly prepared input must preserve the declared boundary.
Confirm the executor cannot fetch history from remotes or credentials added for
publication, including during later corrections.

Push reviewed branches to the disposable bare remote; verify base, final tree,
ancestry, and commit order from the receiver. Walk the result through
[PR publication](../../../../../../pull-requests.md): intended repository and
base, orchestrator-owned credentials, ready PR after review, latest-head CI,
and maintainer merge. Local transport is not proof of GitHub behavior; disclose
that limit. A live GitHub smoke test needs separate maintainer approval naming
destination and cleanup. This Work grants no executor push authority.

## Acceptance

- **AC-1 TODO** Actual transfer and direct-publication probes record whether
  generated changes and the required commit sequence are preserved, with
  inspectable revisions, metadata, trees, and ancestry at the unchanged base.
  Demonstrate the integrated executor path when dependencies permit; otherwise
  record the dependency blocker and independent fixture limits.
  Verification: inspect the available executor or fixture artifact and receiver;
  compare candidate results and record rejected or lossy transfers.
- **AC-2 TODO** Advanced-base, conflict, correction, and missing-ancestry probes
  report observed success or failure, source exposure, and preservation or loss
  of commit and evidence boundaries; unavailable integrated checks cite the
  established dependency blocker.
  Verification: inspect rebase fixtures, source-denial probes after publication
  setup, and the receiver's rejection when base ancestry is missing.
- **AC-3 TODO** A recommendation explains whether main-repository import is
  needed and selects a commit and publication path accounting for PR ownership,
  credentials, CI, recovery, and untested GitHub behavior.
  Verification: trace generation through review, transfer or direct push, and
  the PR procedure; review candidate pros, cons, and limitations.

Preserve reports and promote lasting findings to the parent's named owners.
This Investigation does not implement production delivery or publish live trial
PRs without the separate approval above.
