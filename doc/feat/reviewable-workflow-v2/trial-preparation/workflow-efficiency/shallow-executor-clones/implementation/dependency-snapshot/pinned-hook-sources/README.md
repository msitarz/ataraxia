# Pinned third-party hook source selection

Select the third-party hook sources required by the pinned repository hook
configuration from the dedicated prepared cache under the parent's
[cache boundary](../README.md). Verify origins and resolved pinned revisions;
do not infer provenance from cache directory names. Return selected relative
entries, verified origin/revision provenance and the supported condition to
[snapshot delivery](../snapshot-delivery/README.md).

Retain only the source and Git metadata necessary for offline hook recreation.
Reject or exclude unrelated refs/objects, project payloads, answers/source
references, old hook environments, interpreter/environment metadata and external
links. Do not mutate the raw cache, rewrite opaque metadata, fetch missing
sources, or overwrite a destination. Registry resolver dependencies belong to
the independent [registry selector](../registry-cache-selection/README.md).

Use the parent's linked tested recipe to define the initial pinned
tool/platform/cache-layout condition; unsupported conditions fail closed with no
online fallback. Keep implementation, tests and usage documentation within a
five-minute review; split before expansion. Production execution awaits the
revised plan's review and merge.

## Acceptance

- **AC-1 TODO** Supported prepared hook repositories yield the required pinned
  third-party sources and necessary Git metadata with verified origin/revision
  provenance, excluding unrelated or contaminated inputs without cache mutation.

  Validation: Criterion-marked tests cover allowed and wrong origins/revisions,
  unrelated refs/objects, project/source-reference contamination, old hook
  environments, external links and input immutability. Independently review the
  necessary Git/source boundary; snapshot delivery validates fresh offline hook
  recreation using the composed result.
- **AC-2 TODO** Missing sources, changed hook declarations and unsupported
  tool/platform/layout conditions fail with recoverable diagnostics and retained
  evidence without fetching sources or overwriting destinations.

  Validation: Criterion-marked failure tests exercise each condition and any
  selection destination collision. Independently review supported conditions
  and whether diagnostics identify the missing preparation.
