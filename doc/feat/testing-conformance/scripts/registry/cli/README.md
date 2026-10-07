# Registry CLI integration cases

After observations, move only four CLI functions from
unit/test_registry_selection.py to integration. Preserve successful
manifest/source state, missing-record recovery artifact, existing-destination
sentinel and forbidden cache destination. Assert literal failure bytes/content
independently; stderr/artifact equality is a separate forwarding assertion.
Follow [parent ownership, sequencing and checks](../README.md).

- **AC-1 TODO** Given accepted or invalid disposable inputs, real CLI delivers
  the reviewed manifest or exact refusal/recovery effects while preserving
  complete relevant input/output state.

  Validation: Run four marked integration cases and remaining selector units;
  review original covers/full text, strict inclusion, independent
  artifacts/exits and Make consumers; lint/format, doc/ac and latest CI.
