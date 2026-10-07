# Record validation unit contracts

After selectors, move/clean only digest, dependency declarations, reviewed
evidence and accepted preparation cases from test_registry_validations.py with
their owned literal record fixtures. Preserve complete inventories/record
values, extra/missing keys and acceptance-digest refusals. Expected records must
not be computed by production validators. Follow
[parent ownership, sequencing and checks](../README.md).

- **AC-1 TODO** Given literal record inputs, validators preserve complete
  accepted values and exact errors/causes for missing, extra or unaccepted
  declarations/evidence/bytes.

  Validation: Run marked record cases and remaining registry consumers; review
  independent records, precise fixture types/normal includes, lint/format,
  doc/ac and latest CI.
