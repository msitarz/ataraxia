# Pinned registry cache selection

Select registry dependencies from a dedicated cache prepared by the actual
pinned Make setup/hook contracts, under the parent's
[cache boundary](../README.md). Own the bounded adapter for the tested uv cache
condition, including the project and hook resolver caches. Do not build a
generic cache framework or prepare dependencies online.

The selector validates an independently accepted preparation record, with the
expected record digest supplied separately by its orchestrator owner. Actual
successful Make preparation evidence grounds package origins and complete
inventories, including frozen dependencies outside the project lock. Hash and
METADATA checks preserve that reviewed provenance; they do not authenticate
arbitrary caches or substitute for independent allowed-boundary review. See
[usage](../registry-selection.md).

Return selected relative files/links, pinned package provenance and the
supported tool/index/platform/layout condition for
[snapshot delivery](../snapshot-delivery/README.md). Preserve complete necessary
resolver/index and HTTP metadata without rewriting opaque records. Establish
payload provenance against declared dependencies; matching filenames, hashes or
absence of source-path strings alone are insufficient. Exclude project
editable/build/local-source payloads, answers/source references and
interpreter/environment metadata. Leave the raw cache unchanged; do not copy to
an existing destination or accept links resolving outside the selected cache.

Use the parent's linked tested recipe to define the initial supported condition;
explicitly reject different or unsupported inputs without network fallback.
Pinned hook Git sources belong to the independent
[hook selector](../pinned-hook-sources/README.md). Each leaf delivery, including
tests and usage documentation, must fit a five-minute review; split before
expansion.

## Acceptance

See [local evidence and replayable derivation](evidence.md) for independent
review and the supported preparation boundary.

- **AC-1 DONE** A prepared supported cache yields only declared pinned registry
  payloads with inspectable provenance and complete necessary resolver metadata
  from both resolver caches, excluding contaminated project/environment inputs
  without modifying the raw cache.

  Validation: Criterion-marked tests cover pinned and undeclared packages,
  editable/local-source contamination, both cache roots, metadata retention,
  external links and input immutability. Independently review how provenance and
  metadata completeness are established; snapshot delivery validates actual
  offline resolution of the composed result.
- **AC-2 DONE** Absent artifacts, stale dependency declarations and unsupported
  tool/index/platform/layout conditions fail with recoverable diagnostics and
  retained evidence, without online fallback or destination overwrite.

  Validation: Criterion-marked failure tests exercise each condition and any
  selection destination collision. Independently review the explicit supported
  boundary and whether failure evidence identifies the required preparation.
