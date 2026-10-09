# CLI testing conformance

## Delivery map

- **TODO** [Reporting arrangements](arrangements/README.md): typed result inputs
  and independent full serialization expectations before consumers.
- **TODO** [Reporting units](reporting/README.md): real display/save outcomes.
- **TODO** [Argument-only units](arguments/README.md): actual parser exits
  before backtesting, without an internal product double.
- **TODO** [Command support](command/README.md): isolated typed shipped-command
  execution before acceptance flows.
- **TODO** [Sample golden artifacts](golden/README.md): independently derived
  complete sample results before their acceptance consumer.
- **TODO** [Success flow](success/README.md): exact report and complete
  artifact.
- **TODO** [Failure flows](failures/README.md): exact exits, diagnostic context
  and absent/unchanged output, including the migrated empty-result case.

Merge this map before implementation; deliver leaves in listed order. Paths
below are relative to `test/ataraxia`. Serialize strict includes, helper/fixture
ownership, legacy subsets and maps. Every cleaned module/helper/executable
fixture is precisely annotated and explicitly normal strict checked; do not
imply adoption of untouched remainders or alter positive/negative type-check
routes. No forward fixture dependency, broad typing suppression, shared conftest
migration, production repair or property adoption. Full supporting changes count
toward five-minute leaf review; split and review revised maps before expansion.

Preserve the three existing unit cases, sample success and twelve failure rows
with their inputs/identities/markers. Keep legacy tests until their real
replacements deliver. Use concise slice docstrings and Given/When/Then. Retain
all failure rows here; any later duplicate reduction first requires reviewed
lower-level malformed-input coverage and preservation of distinct user outcomes.
Each leaf runs focused cases/affected remainders, strict typing, lint/format and
doc/ac checks; latest-head full CI remains required before merge.

- **AC-1 TODO** Given completed CLI deliveries, retained reporting/parser/user
  flows exercise real public behavior, complete independent artifacts and exact
  exits/failure state, preserving provenance and precise incremental typing
  without patched backtesting or weakened lower-level malformed-input coverage.

  Validation: integrate independent child reviews and case inventories; run all
  CLI modules, complete product suite and strict checks, and require latest-head
  full CI. Planning or fixture declarations alone do not verify this outcome.
