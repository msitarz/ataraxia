# Engineering conventions

Read the [repair and scope rules](change-rules.md#fix-the-underlying-problem)
for any repository change. Read the rest when changing or reviewing code or
tests. Use [check and evidence policy](validation.md) when choosing checks or
reporting evidence and [architecture](architecture.md) for current system
contracts.

## Fix the underlying problem

See [Repair and scope rules](change-rules.md#fix-the-underlying-problem).

## Code style

[Ruff configuration](../pyproject.toml) owns formatting, imports, and docstring
checks; [EditorConfig](../.editorconfig) owns file whitespace and encoding.
Use four-space indentation, 88-character lines, double quotes, Google-style
docstrings, `snake_case` functions/modules, and `PascalCase` classes. Satisfy
strict Pyrefly and add `# SPDX-License-Identifier: Apache-2.0` to new source
files.

- Prefer function composition, focused functions, guard clauses, and early
  returns. Ruff's PLR0915 counts statements in source, scripts, and tests:
  26–50 statements are advisory and more than 50 blocks lint. Treat about 25
  statements as a review signal; these counts guide readability review, not
  function shape. Don't split code only to lower a count. Extract cohesive
  helpers that improve readability.
- Inject dependencies through arguments or constructor/dataclass fields.
- Depend on structural `typing.Protocol` contracts for collaborators; value
  objects/internal helpers need not have protocols. Use `@runtime_checkable` for
  runtime checks; see `compute/protocol.py` and `provider.py` under
  `src/ataraxia/`.
- Model records with dataclasses; prefer `frozen=True` for values and node
  specifications, and `field(default_factory=...)` for per-instance
  containers/collaborators. Keep specifications hashable and execution state in
  runners; see `source.py` and `feature.py`.
- For dictionary records, use `TypedDict` (`BrokerReturn`,
  `BacktestShardReturn`); reserve typed `Mapping[K, V]`/`MutableMapping[K, V]`
  for dynamic keys such as nodes or dependency names.
- At library boundaries, translate expected low-level failures into contextual
  exceptions in `src/ataraxia/errors.py`. Derive from `AtaraxiaError`, retain an
  appropriate built-in base, and preserve causes:
  `raise DomainError("Useful context") from exc` (see `sort_graph`). Don't
  blanket-wrap programming errors or normal iteration termination. Document
  caller-handled domain errors in Google-style `Raises` sections.
- Node pattern: `deps()` names inputs, `factory()` supplies a runner, and runner
  `__call__` computes. Match dependency keys to runner parameters. Extract
  reusable calculations, as `SmaRunner` does with `sma`.
- Use modern typing: `T | None`, built-in generics, `type` aliases,
  parameterized protocols/classes, and `Literal` for closed sets (signal sides).
  Prefer `collections.abc` contracts (`Sequence`, `Mapping`, `Iterator`);
  require mutability only when needed.
- Use context managers for files/providers, preserving source/provider lifecycle
  delegation and cleanup on success/failure; use `pathlib.Path`.
- Keep console output in `src/ataraxia/cli.py`; libraries return values or raise
  domain errors.

### Preserve type precision

Type precision is part of correctness. Passing strict Pyrefly is necessary, but
does not justify losing information about values or their relationships.

- Never resolve a mismatch by widening a meaningful type to `Any`, `object`, an
  unparameterized container, or a base type that discards the required contract.
  Do not remove annotations or add catch-all union members to make incompatible
  values fit. Existing broad types are debt, not precedent for spreading them.
- A repository-owned, reviewed static expectation loaded only as an opaque
  fixture may use `object` honestly. This does not justify widening a meaningful
  structured contract; see
  [test data guidance](testing.md#treat-test-data-as-data).
- Introduce types or explicit unions of supported variants as needed to model
  the contract. Preserve input/output relationships with type parameters through
  producers, runners, consumers, and containers. A type parameter must be
  determined by a typed input or owning instance; an unconstrained return-only
  parameter does not establish safety.
- When annotations and behavior disagree, determine the intended supported cases
  and update the affected call chain coherently. Do not retain a false narrow
  annotation, silently drop supported behavior, or substitute a broad return
  type followed by caller-side runtime checks. Creating an appropriate type or
  separating distinct operations is preferable to erasing the distinction.
- Keep unavoidable untyped input at the external boundary. Validate or adapt it
  there into an explicit project contract before it enters application code. Do
  not expose that uncertainty through public result types. Casts,
  `TypeGuard`/`TypeIs`, ignores, and disabled diagnostics must not conceal a
  mismatch or replace a missing type model; narrowing predicates must actually
  establish their claimed contract.
- Use named `Literal` aliases for intentionally finite string domains when
  consumers benefit from static rejection. Give domains with different meanings
  distinct names even when their members overlap; aliases still describe
  structural value sets, not nominal identities. An annotation does not validate
  a runtime object: at the consumed external boundary, first establish that the
  input is a `str`, then validate it against the intended domain and reject
  unsupported values before passing the narrow result to consumers. Keep `str`
  for open defaults, paths, hashes, plugin keys, extensions, and overlapping
  classifications where future or dynamic values are accepted.

  For a flat `Literal` alias, a domain-specific `TypeIs` predicate can derive
  runtime membership from the alias and keep one authoritative inventory:

  ```python
  from typing import Literal, TypeIs, get_args

  type ChangedInput = Literal["declaration", "file"]
  type RecordName = Literal["accepted", "version"]

  def is_changed_input(value: str) -> TypeIs[ChangedInput]:
      return value in get_args(ChangedInput.__value__)

  def is_record_name(value: str) -> TypeIs[RecordName]:
      return value in get_args(RecordName.__value__)

  def changed_input(value: object) -> ChangedInput:
      if not isinstance(value, str):
          raise ValueError("changed input must be a string")
      if not is_changed_input(value):
          raise ValueError("unsupported changed input")
      return value

  def record_name(value: object) -> RecordName:
      if not isinstance(value, str):
          raise ValueError("record name must be a string")
      if not is_record_name(value):
          raise ValueError("unsupported record name")
      return value

  def consume_changed_input(value: ChangedInput) -> str:
      return f"changed:{value}"

  def describe_change(value: ChangedInput) -> str:
      match value:
          case "declaration":
              return "update declaration"
          case "file":
              return "replace file"

  changed = changed_input("file")
  record = record_name("accepted")
  consume_changed_input(changed)
  describe_change(changed)
  ```

  `TypeIs` is a soundness promise: its predicate must establish exactly the
  claimed membership. The repository's supported Python environment checks this
  flat PEP 695 alias metadata pattern with `get_args`; use it only when one
  authoritative inventory improves clarity. When members need distinct actions,
  an alternative is a boundary decoder with one `match` case per supported
  string, returning that value as `ChangedInput`, and a `ValueError` default for
  other strings. Its repeated
  cases must be checked against the alias and cover every supported member.
  `describe_change` then accepts the validated alias and selects actions without
  handling raw input. Do not add a parallel set or registry. An open-string
  consumer may intentionally return a default such as `"text"` for other
  values, thereby accepting future values. That is appropriate for open `str`,
  not evidence of a closed domain. Dynamic plugin names and prefix-based
  classifications may be unbounded or overlap, so keep those as `str` and
  preserve their fallback behavior.

  The boundary rejects `changed_input(3)` because it is not a string,
  `record_name("file")` because the name belongs to the other domain, and
  `changed_input("future-option")` because it is unknown. Each raises
  `ValueError` before reaching a consumer. Static typing also rejects an open
  `str` and an unsupported Literal value at a finite consumer, for different
  reasons:

  ```python
  def rejected_calls(open_value: str) -> None:
      consume_changed_input(open_value)  # Rejected: str was not validated.
      consume_changed_input("future-option")  # Not a ChangedInput member.

  ```

  Use an `Enum` when member identity or behavior is useful and the runtime API
  should use members. Constructing `Kind(value)` validates wire strings, but
  callers then receive enum members and serialization must convert back to
  strings. For ordinary selectors, `Literal` retains the string runtime API with
  less conversion. See [testing guidance](testing.md) for boundary and
  type-checking test ownership; annotations alone prove neither runtime
  validation nor sound narrowing.

  Configured Ruff does not identify closed string domains. The pinned Pyrefly
  check produced a hidden warning for an incomplete Literal match and exited
  successfully, so it is not an actionable completeness gate. See the historical
  [Literal selection investigation](https://github.com/msitarz/ataraxia/blob/811c4de0943b2faf9877ffd4471125fbd77bf92c/doc/feat/literal-selection/investigation.md)
  for the executed evidence and its version limits. This does not require a
  linter, checker migration, or exhaustive matches for intentionally open
  domains.
- Verify both behavior and static guarantees. Run strict Pyrefly and inspect the
  affected signatures and inferred types; for generic or variant contracts, add
  focused type-checking cases that demonstrate precise results and rejection of
  invalid uses. Runtime tests and a green checker alone do not prove that useful
  type information was preserved.

## Structural review

After each small change, inspect new types, repeated fields and behavior, and
module placement. Fold structures with the same meaning into one type. When
variants need distinct types but repeat fields or behavior, consider a shared
base class or helper; this applies to diagnostic records as well as success and
failure records. Move code to the module that owns its responsibility. Extract
only when the resulting contract is clearer, and explain in the PR when
intentional overlap should remain.

## Testing guidelines

When writing, changing, or reviewing tests, read [Testing](testing.md) and its
relevant test-type guidance. Read [Test ownership](test-ownership.md) when
reviewing tests for cleanup.
