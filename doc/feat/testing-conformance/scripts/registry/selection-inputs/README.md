# Prepared selection inputs

After transport, isolate PreparedSelection, literal input filesystem/record
variants, changed-input and collision arrangements plus their owned fixtures.
Preserve fresh copies, accepted digest provenance and complete bytes/link
targets. Keep record/payload validator fixtures outside scope; no
process/manifest reader redesign. Follow
[parent ownership, sequencing and checks](../README.md).

- **AC-1 TODO** Given fresh accepted or damaged named inputs, arrangements
  expose precisely typed paths/data and the independent preparation acceptance
  digest without changing shared source fixtures.

  Validation: Run all selection consumers; independently inspect literal
  fixtures and fresh-copy/state isolation, precise types/normal inclusion, Make
  registry checks, lint/format, doc/ac and latest CI.
