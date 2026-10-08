# Value and trading-rule test conformance

## Delivery map

- **DONE** Bar outcomes: complete public normalization and range boundaries;
  retain the delivered strict-typing pilot.
- **TODO** [Rolling windows](rolling/README.md): newest-first runner state and
  typed node construction.
- **TODO** [SMA outcomes](sma/README.md): warm-up, missing/zero values, errors,
  and actual bar-close calculation instead of a patched internal function.
- **TODO** [Positions](positions/README.md): both sides, price equality/gaps,
  competing orders and retained closing state.
- **TODO** [Broker/account](broker/README.md): complete snapshots and account
  sums, existing-position updates and prevention of same-bar exits.

Merge this map before implementation; deliver leaves in listed order. Shared
Pyrefly includes and map edits are serial. Each leaf owns its stated subset;
leave remaining legacy cases unchanged until their owner adopts them. Keep
fixtures module-local, with no forward dependency or blanket conftest migration.
Every cleaned module/helper is precisely annotated and explicitly strict
checked. Preserve cases, markers and session-authorized slice docstrings.

Run each leaf's focused cases and affected legacy remainder, strict typing,
lint/format and doc/ac checks; require latest-head full CI before merge. Split
supporting fixture/type migration before expanding beyond five-minute review.
Unexpected contract/type mismatches need a separately scoped repair; do not
weaken expectations, widen types, or change production to complete cleanup.

- **AC-1 TODO** Given all delivered leaves, value/trading tests preserve literal
  outcomes and boundary cases through real public behavior with precise typing.

  Validation: independently review leaf artifacts, case inventories and focused
  execution; run the complete product suite and strict typing after integration.
