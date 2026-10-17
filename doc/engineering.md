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
- Use `match` when one stable value selects among distinct cases and only one
  case should run; preserve required unmatched-input behavior. Keep independent
  `if` statements when multiple conditions may apply, and use guard clauses or
  simple `if`/`else` when clearer. A dictionary lookup can suit a pure mapping
  from keys to fixed values.
- Do not nest `try` statements within the same execution scope, including
  through branches or loops and inside `except`, `else`, or `finally`; this
  applies equally to `async` functions and `except*`. Sequential `try`
  statements are allowed when they protect distinct operations. Separate nested
  function or method scopes with `try` statements are allowed. Use context
  managers for resource cleanup and extract cohesive helpers that preserve
  operation-specific catches, exception causes, cleanup, and resource ownership.
  Do not split code into tiny helpers merely to avoid nesting.
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
- Use named `Literal` aliases for intentionally finite string domains. At the
  consuming boundary, validate that external input is a string and a supported
  member before passing it to typed logic. Annotations alone do not validate
  runtime data.

  For a flat PEP 695 alias, a domain-specific `TypeIs[Domain]` predicate can use
  value in `get_args(Domain.__value__)` to share one authoritative member
  inventory. The predicate must establish the membership it claims; repeated
  action cases must cover every supported member. Keep str and meaningful
  defaults for open domains—match arms and test values alone do not establish
  closure.
- Use a discriminated union when a validated internal lifecycle value has
  genuinely different variant fields and consumers make typed decisions from
  one variant at a time. Keep shared ownership and identity in a product record,
  and keep raw JSON parsing, complete consumed-field and cross-field validation,
  and JSON serialization at the boundary. A flat `TypedDict` can remain the
  better transport and incremental-update shape; a tagged `TypedDict` union is
  another transport option when variant-specific required keys help callers.
  Neither `TypedDict` nor frozen dataclasses enforce runtime values, and frozen
  records are shallow when they contain mutable dictionaries. A sandbox-marker
  comparison found the clearest split to be a flat validated record at the
  persistence/update boundary and a dataclass lifecycle union only for internal
  decisions. Pyrefly 1.3.1 narrows both dataclass and tagged `TypedDict` unions
  when matching the discriminant and reports an omitted variant through
  `assert_never`; matching the entire `TypedDict` with a mapping pattern did not
  produce useful narrowing. `match` still needs an explicit exhaustive check;
  an `int()` class pattern also accepts `bool`, so runtime validation must
  exclude it where the domain requires a true integer.
- Verify both behavior and static guarantees. Run strict Pyrefly and inspect the
  affected signatures and inferred types; for generic or variant contracts, add
  focused type-checking cases that demonstrate precise results and rejection of
  invalid uses. Runtime tests and a green checker alone do not prove that useful
  type information was preserved.

### Lifecycle representation fit

The sandbox-marker comparison used the complete persisted record in the
[pinned seed at 47779e4](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L38-L92)
as its boundary: schema, generation, owner, state, all four optional failure
strings, destination device and inode, and JSON-compatible extension fields.
Validate that whole record before passing lifecycle data to a pure decision. The
decision does not need to inspect schema or ownership, but they still identify
the persisted value. Keep current filesystem identity and held-lock freshness
checks at their effectful adapter boundaries.

| Representation | Fit | Tradeoffs |
| --- | --- | --- |
| Frozen dataclass union | Best for validated internal decisions with variant-only fields. Shared owner and destination identity stay in a product record; `Failed` owns one four-string diagnostic value. | Makes variant handling and immutable replacement clear, but needs boundary parsing and flattening for JSON. Annotations do not validate construction; `frozen=True` is shallow, so extension data needs explicit ownership or copying. Updating state replaces the lifecycle value. |
| Tagged `TypedDict` union | Useful when the serialized mapping itself is the application value and each variant's required keys help typed callers. | Fits JSON and mutable updates naturally, but construction does no runtime validation and mutable ownership remains explicit. A discriminant match narrows reliably; a mapping-pattern match on the whole union did not in the checked example. |
| Flat record with `Literal` state and optional diagnostics | Best for the pinned seed marker's persistence and incremental update boundary. It serializes directly and matches that seed's `SandboxChanges` patch shape. | Does not encode the relationship between state and diagnostics in its type, so the complete boundary validator must reject missing failed diagnostics and diagnostics on other states. Consumers see optional diagnostic fields. |

For example, a validated core decision can accept a sum while transport stays a
product record:

```python
@dataclass(frozen=True)
class FailureDiagnostics:
    stage: str
    status: str
    stdout: str
    stderr: str


@dataclass(frozen=True)
class Preparing:
    pass


@dataclass(frozen=True)
class Ready:
    pass


@dataclass(frozen=True)
class Failed:
    diagnostics: FailureDiagnostics


type Lifecycle = Preparing | Ready | Failed


def failure_details(state: Lifecycle) -> FailureDiagnostics | None:
    match state:
        case Failed(diagnostics=details):
            return details
        case Preparing() | Ready():
            return None
        case _:
            assert_never(state)
```

This is a product of shared marker fields and a sum of lifecycle alternatives;
it adds no lifecycle rules. Boundary validation still checks required field
types, excludes Boolean and negative destination integers, enforces diagnostic
presence, and preserves extensions. Independent constraints are clearer as
separate guards than as a dense `match` guard. On the pinned seed, a one-time
runtime probe through
`make test ARGS=test/script/unit/test_adt_investigation_probe.py` covered valid
serialization roundtrips, invalid consumed fields and cross-field combinations,
extension preservation, `TypedDict` construction, shallow frozen contents, and
the `int()` pattern accepting `bool` (7 passed).
`make typecheck-expectations ARGS=test/script/typecheck/algebraic_data_types_probe.py`
showed precise decision result types and expected missing-variant errors for
both dataclass and tagged `TypedDict` unions under locked Pyrefly 1.3.1. The
temporary probe files are removed after recording these methods and outcomes;
they are adoption evidence, not ongoing regression coverage.

The seed comparison recommends keeping the flat record for persistence and
incremental updates, with a dataclass lifecycle union only if internal pure
consumers need variant-specific decisions. It does not justify changing the
current sandbox implementation or adopting a general representation rule for
unrelated data.

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
