# Safe offline dependency snapshot

Own optional Make-controlled selection and immutable manifest of dependencies
from a dedicated cache prepared by actual pinned Make setup/hook contracts.
Preserve resolver/index metadata and vetted pinned third-party hook sources. Do
not copy project Git/build/editable payloads, answers/source references, old
virtual environments, interpreter/environment metadata or external links. Raw
caches remain unchanged; selection is filter-on-copy, never blind metadata
rewriting. See the
[cache recipe](../../sandbox-isolation/successful-recipe.md#project-setup-through-make-with-fresh-offline-environments).

Keep this leaf within a five-minute review; split before oversized execution.
Automated tests use criterion markers scoped to this README; manual judgments
remain independent review. All criteria are planned, not observed evidence.

## Acceptance

- **AC-1 TODO** A prepared cache produces a hash/provenance inventory and
  snapshot containing only declared pinned dependencies and complete resolver
  metadata; project payloads, source references, old environments and external
  links are rejected or excluded without changing the input cache.

  Validation: Criterion-marked selection tests cover contaminated inputs, pinned
  hook origins/revisions, links, metadata retention and input immutability;
  independently review provenance and the allowed dependency boundary.
- **AC-2 TODO** Missing, stale or unsupported cache/index inputs produce a
  recoverable diagnostic and retained destination/evidence without network
  fallback or destructive overwrite.

  Validation: Criterion-marked failure tests
  include absent artifacts, changed manifest and an existing destination;
  independently review the supported cache/platform condition.
