# Manifest adaptation and selector observations

Own ManifestObservation, read_manifest, expected_manifest, expected_selection,
select_prepared and selection_expected/manifest_expected fixtures. Adapt exactly
the five public manifest fields, nested string maps and eight package fields
through precise supported types. Reuse existing JSON adaptation where it fits;
validate consumed shapes without production-record/package validation or a
new generic framework. Expected values still come from the independent literal
manifest, not running production selection/validators. Follow
[parent ownership and sequencing](../README.md).

- **AC-1 DONE** Given literal or delivered manifest data, observations retain
  every public value through precise canonical types and reject malformed
  consumed shapes before exposing typed values; real public selector calls
  preserve the independent complete expected result and input state.

  Validation: Run marked whole-value and malformed-shape cases with independent
  expectations, existing selector/CLI and Make registry consumers; review JSON
  precision, oracle independence and owned fixture boundaries. Include extracted
  helpers/fixtures and cleaned tests precisely in normal strict checking; run
  lint/format, doc/ac and latest full CI. Preserve original cases/covers and
  stop/split before exceeding five-minute complete review.
