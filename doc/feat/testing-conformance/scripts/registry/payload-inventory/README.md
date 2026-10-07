# Payload inventory and vendored metadata

After layout, isolate package_payload cases and only their payload/vendored
fixtures. Preserve complete entries, one owning METADATA, resolver HTTP
metadata, trace/basis and nested vendored data without using production to
derive expected PackagePayload. Follow
[parent ownership, sequencing and checks](../README.md).

- **AC-1 TODO** Given literal payload inventories, complete public payload
  values retain vendored entries and each missing/contradictory inventory fails
  precisely.

  Validation: Run marked payload-inventory cases; review whole literal expected
  values, named fixture ownership and strict includes, remaining registry/Make
  consumers, lint/format, doc/ac and latest CI.
