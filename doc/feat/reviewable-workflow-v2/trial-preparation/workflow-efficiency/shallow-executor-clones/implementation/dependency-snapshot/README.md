# Safe offline dependency snapshot

Own optional Make-controlled selection and immutable manifest of dependencies
from a dedicated cache prepared by actual pinned Make setup/hook contracts.
Preserve resolver/index metadata and vetted pinned third-party hook sources. Do
not copy project Git/build/editable payloads, answers/source references, old
virtual environments, interpreter/environment metadata or external links. Raw
caches remain unchanged; selection is filter-on-copy, never blind metadata
rewriting. See the
[cache recipe](../../sandbox-isolation/successful-recipe.md#project-setup-through-make-with-fresh-offline-environments).

## Child Works and composition

- **DONE** Optional reviewed registry selection verifies pinned registry
  payloads and preserves their complete resolver metadata; see
  [usage](../../../../../../../../CONTRIBUTING.md#optional-reviewed-registry-selection)
  and
  [verified evidence](https://github.com/msitarz/ataraxia/blob/6a0e4c0e5d65cd4fea48a3b887f5187d30868402/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/implementation/dependency-snapshot/registry-cache-selection/evidence.md).
- **TODO** [Pinned hook sources](pinned-hook-sources/README.md): verify and
  select only the required pinned third-party hook sources.
- **TODO** [Snapshot delivery](snapshot-delivery/README.md): compose both
  selections into a frozen snapshot with safe copying and recoverable failures.

Registry and hook selection can proceed independently. Each returns its selected
relative entries, dependency provenance and supported condition to snapshot
delivery; that child depends on both reviewed results. Define concrete formats
with implementation rather than introducing a general cache framework. Delivery
must validate the composed snapshot through actual fresh offline Make setup;
hashes and path scans alone cannot establish safe provenance or completeness.

Each child owns criterion-marked tests and aims at a five-minute review
including tests and documentation. Reassess and split before oversized
execution. Merge this revised map before production implementation. This
planning correction changes no preparation policy and authorizes no network or
model launch. All criteria are planned, not observed evidence.

## Acceptance

- **AC-1 TODO** A prepared cache produces a hash/provenance inventory and
  snapshot containing only declared pinned dependencies and complete resolver
  metadata; project payloads, source references, old environments and external
  links are rejected or excluded without changing the input cache.

  Validation: Reuse reviewed child selection tests and provenance evidence;
  criterion-marked composition tests and actual fresh offline Make setup verify
  the delivered snapshot. Independently review the composed allowed dependency
  boundary and retained input-immutability evidence.
- **AC-2 TODO** Missing, stale or unsupported cache/index inputs produce a
  recoverable diagnostic and retained destination/evidence without network
  fallback or destructive overwrite.

  Validation: Reuse reviewed child failure tests for absent artifacts, changed
  manifest, unsupported conditions and an existing destination. Independently
  review supported conditions and retained recovery evidence, including the
  composed snapshot's actual offline missing-artifact failure.
