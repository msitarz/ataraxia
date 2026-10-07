# Selection process and manifest observations

Separate external manifest adaptation from real CLI process/state isolation so
each complete delivery fits the five-minute review boundary. Follow
[parent ownership, sequencing and checks](../README.md).

- **DONE** Precise canonical manifest adaptation, independent whole-value oracle
  and typed public selector/expected-fixture observations.
- **TODO** [CLI process and complete state](process-state/README.md).

Manifest adaptation is delivered; process/state follows. Sequence shared
support/conftest, consumer imports and strict includes. The first child owns
ManifestObservation, read_manifest, expected_manifest, expected_selection,
select_prepared and the two expected-value fixtures. The second owns
SelectionProcessResult, tree_state and run_selection_cli. Preserve existing
consumer paths/cases/markers, with narrow typed reexports if needed; no CLI case
relocation in this subtree. Validator fixtures and the single-read double remain
for later leaves.

- **AC-1 TODO** Given prepared inputs, actual selector/CLI observations retain
  complete manifest fields, file bytes/link targets, exit and diagnostics
  through precisely typed results.

  Validation: Run existing selector/CLI and Make registry consumers; review
  literal oracle independence and JSON precision, strict owned-helper/fixture
  inclusion, lint/format, doc/ac and latest CI.
