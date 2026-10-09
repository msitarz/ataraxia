# Reconcile static-fixture validation guidance

Own the revision at `doc/testing.md`'s Treat test data as data section and a
narrow clarification of `doc/engineering.md`'s Preserve type precision section.
The rule applies equally to `test/ataraxia`, `test/make` and `test/script`.
Repository-owned reviewed static expectations prefer complete comparison with
actual values; add schema/content validation only when structured consumer
access, genuinely external data or an independent validation contract needs it.
Limit validation to that actual need.

For a loaded value used only in whole-value equality, `object` honestly states
the opaque comparison contract. Distinguish that from widening a meaningful
structured input/output contract to object/Any or using casts/ignores. Do not
invent detailed schemas solely to satisfy strict typing. Preserve necessary
production/consumer validation, type relationships and independent expected
oracles; complete comparison must still detect missing or unexpected fields.

Reconcile only the directly conflicting active CLI arrangements/golden wording
under `doc/feat/testing-conformance/ataraxia/cli/`: loading a reviewed static
JSON file does not itself make the fixture external or require a second
validator. Path adaptation or structured access still owns its needed checks.
These local contracts link to the common owner instead of repeating a competing
rule. Coordinate their shared edits serially with ongoing CLI deliveries; if a
contract has been delivered, do not restore it or rewrite accepted history.

Preserve the parent's #244 example/rationale. No test/code/configuration edits,
PR #244 mutation, blanket loader cleanup or new type-check route belongs here.
Keep the complete guidance diff within five-minute review; return a split before
adding independent cleanup. Session adoption does not verify durable delivery.

- **AC-1 DONE** Given revised common owners and active CLI contracts, guidance
  consistently permits opaque equality expectations, requires only justified
  validation, and preserves meaningful structured typing and genuine validation
  boundaries without duplicated policy or weakened full-value oracles.

  Validation: manually trace the testing/engineering and active CLI reading
  routes; compare static equality, path adaptation, structured access and
  external validation examples. Run doc-format, doc-check and ac-check; require
  latest-head full CI before merge. Keep unsupported criterion outcomes TODO.
