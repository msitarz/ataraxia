# Remove unnecessary validation of static golden expectations

Scan golden-loading paths in `test/ataraxia`, `test/script` and `test/make`
against [test data guidance](../../../testing.md#treat-test-data-as-data).
Remove validation used only to reconstruct a reviewed static expectation for
whole-value equality. Preserve independent expected values, complete equality
that detects missing/extra fields, case identities, parametrization, markers,
fixture bytes and precise meaningful contracts. A justified no-change finding
is an acceptable outcome for any suite; do not force edits in all three.

## Bounded ownership

The initial scan found one concrete opaque-equality candidate:
`test/script/unit/test_registry_records.py` loads `preparation_expected` through
`read_fixture` but only compares it with `accepted_preparation`'s complete
result. Own that expected value and its consuming test here. Before:
`preparation_expected() -> dict[str, Json]` recursively adapts every field.
After: the test's Given phase directly loads the reviewed static JSON as
`object` for complete equality, without recreating its schema or retaining a
single-use fixture. The production result remains precisely typed and its
digest/refusal cases remain unchanged. This small change needs this prose
summary, not an invented diagram/API.

Inspect other loaders and their consumers before prescribing edits. In
`test/script/record_variants.py`, `read_fixture`/`json_value` support named
record mutation and untouched recursive JSON preservation: retain the necessary
structured adaptation and its existing cases. In
`test/script/selection_manifest.py`, `expected_manifest` currently shares the
actual manifest adapter and `expected_selection` accesses its typed selection;
retain needed structured access and actual-artifact validation. Do not replace
that meaningful contract with opaque data merely to remove validation.
`test/ataraxia/cli_result_inputs.py` and `cli_sample_expected.py` already load
opaque goldens; preserve actual sample path/order normalization, including all
untouched fields. `test/make/support.py:read_calls` observes external process
records, not a static golden; preserve its typed validation. These are scan
findings, not blanket claims about either suite.

Record a concise scan inventory with loader/consumer, expected versus actual
data, retained checks and rationale in the review evidence. Own only the named
registry-record expectation slice plus this inventory; additional cleanup
findings need reviewed contract/map amendments before implementation. Size the
complete test/helper/type/config change for about five-minute review; escalate
and split before implementing findings that exceed it. Shared helpers, strict
configuration and parent maps are serial edits, with dependency owners ready
before consumers. All changed test/helper/executable-fixture modules must have
precise supported annotations and explicit passing incremental strict inclusion.
Opaque equality may honestly use `object`; no schema recreation, casts, ignores,
`Any` widening or loss of structured precision to satisfy typing.

No production repair, Hypothesis adoption, guidance changes, blanket migration
or testing-conformance parent closure. Preserve external-output, path-adaptation
and independent validation contracts under
[test ownership](../../../test-ownership.md). Use concise slice docstrings.

- **AC-1 DONE** Given the reviewed static expectations and their actual
  consumers across all three suites, the bounded cleanup removes unnecessary
  equality-only validation while retaining complete independent comparisons,
  justified structured/external checks, named cases and precise strict types;
  reviewed no-change findings identify their reasons and any deferred scope.

  Validation: independently inspect the scan inventory, fixture/helper changes
  and retained consumers; run focused registry-record tests and any changed
  consumer tests, strict type checks including changed dependencies, and doc/ac
  checks. Verify complete equality rejects missing/extra fields without adding
  a duplicate fixture-schema validator; review preserved markers/cases.
