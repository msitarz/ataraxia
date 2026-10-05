# Frozen offline snapshot delivery

Compose the independently reviewed
[registry selection](../registry-selection.md)
and [hook source selection](../pinned-hook-sources/README.md) into an optional
Make-owned snapshot utility under the parent's [cache boundary](../README.md).
This Work depends on both selectors. Bind the delivered hash/provenance manifest
to their verified entries, dependency declarations and supported conditions;
recheck selected inputs before copying. Define the concrete interface during
implementation without a general cache framework.

Copy only into new destinations. Validate links within the selected snapshot,
retain complete selected resolver metadata, and reject stale or incompatible
selection inputs. Leave source caches unchanged and retain partial destinations
and diagnostic evidence on failure. No project payloads, answers/source
references, old environments, interpreter metadata or external links may enter
the snapshot. Do not rewrite opaque metadata or fall back online.

Document authoritative usage through Make help and CONTRIBUTING. Validate the
composed result with fresh environments through the actual pinned offline Make
setup and readiness/hook contracts from the parent's linked recipe, retaining
the audit. This establishes composition beyond hash checks and path scans.
Clone construction, sandbox/launch/model integration and import tooling remain
sibling responsibilities; this optional utility changes no preparation policy.
Keep the complete delivery within a five-minute review and split before
expansion. Production execution awaits the revised plan's review and merge.

## Acceptance

- **AC-1 TODO** The Make utility delivers a hash/provenance manifest and
  composed snapshot matching both verified selections; actual fresh offline Make
  setup, readiness and pinned hook recreation succeed under the declared
  supported condition without input cache mutation.

  Validation: Criterion-marked tests exercise composition, manifest binding,
  link containment and input immutability. Retain actual fresh offline Make
  setup/readiness/hook evidence under the linked recipe. Independently review
  provenance composition, resolver completeness and authoritative usage; path
  scans and hashes alone do not satisfy this criterion.
- **AC-2 TODO** Missing artifacts, changed manifests/declarations, incompatible
  supported conditions, external links and existing destinations produce
  recoverable failures with retained evidence/destinations, no destructive
  overwrite and no network fallback.

  Validation: Criterion-marked tests exercise these failures. Retain an actual
  fresh offline missing-artifact setup failure and independently review its
  diagnostic, recovery instructions and preserved destination.
