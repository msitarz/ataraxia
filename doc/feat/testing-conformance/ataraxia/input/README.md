# Input test conformance

## Delivery map

- **TODO** [Provider reads](reads/README.md): real temporary CSVs, complete
  Bars, exhaustion/blank rows and filepath hashing.
- **TODO** [Provider failures](failures/README.md): contextual header/row/parser
  failures, exact causes and real closed-file state.
- **TODO** [Source forwarding](forwarding/README.md): precisely typed Provider
  collaborators, send/factory/runner identity and context argument/result
  routing.
- **TODO** [Source CSV contexts](contexts/README.md): real provider resources on
  exhaustion, body failure and early source-context exit.

Merge this map before implementation; deliver leaves in listed order. Each owns
its named modules/subsets and strict includes; serialize Pyrefly and map edits.
Keep fixtures local, with no shared helper or forward fixture dependency. Every
changed test/helper/collaborator has precise annotations and explicit normal
strict inclusion. Do not claim the untouched legacy remainder is adopted.
Preserve case identities/markers; use session-authorized concise slice
docstrings, Given/When/Then and independent complete expectations.

[ADR 12](../../../../adr/0012-source-node-computable-instance.md) governs
retained source/provider/runner instances;
[ADR 16](../../../../adr/0016-source-manages-its-own-provider-lifecycle.md)
governs context forwarding. Provider exhaustion alone does not close its file;
assert closure after the owning context exits. Early `with SourceNode(...)` exit
is not explicit compute-generator closure. Real compute-generator exhaustion,
runner error and explicit `close()` remain with the future Compute plan. No
production repair, subprocess, property adoption or blanket conftest migration.
Split supporting fixture/type work before exceeding five-minute complete review.

Each leaf runs its focused cases and affected legacy remainder, strict typing,
lint/format and doc/ac checks; latest-head full CI remains required before
merge.

- **AC-1 TODO** Given completed input deliveries, retained provider/source cases
  observe real CSV values and contextual failures, complete independent Bars,
  real resource closure at owned context exits, and faithful public forwarding
  with preserved instance identity/provenance and precise incremental typing.

  Validation: integrate independent child reviews and case inventories; run all
  input modules, the complete product suite and strict type checks, and require
  latest-head full CI. Report unverified paths, skips and exposed contract gaps.
