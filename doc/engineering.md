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

### Validate at boundaries and construction

Validation belongs where uncertainty enters or a value is created. Define the
consumed record as every field and relationship an operation relies on,
including ownership, persistence, and security requirements.

- At raw or untyped ingress, including persisted data, validate the consumed
  structure, runtime types, and relationships before adapting it to a project
  type. Check contract gaps and domain invariants around a documented typed
  library API; rely on its documented guarantees instead of repeating them.
- At trusted typed internal construction, rely on declared argument types and
  already validated child domain values. Enforce the invariants owned by the
  new value, including semantic and cross-field rules, without revalidating
  children or claiming arbitrary untyped-schema validation.
- Check runtime types when the domain or storage contract requires it; for an
  integer domain, exclude `bool` when it is not a valid value. Annotations alone
  never validate raw runtime data.
- Keep consumed ownership, persistence, and security fields in the validated
  record even when one pure decision does not read them. Leave unused extension
  data opaque and preserve it when transport or persistence compatibility
  requires it.
- Keep internal invariant failures concise. At external boundaries, give
  actionable context and distinguish failures when callers need different
  responses; rejecting at the first error is fine. At Ataraxia library API
  boundaries, translate expected low-level library failures into contextual
  exceptions in `src/ataraxia/errors.py`. Derive from `AtaraxiaError`, retain
  an appropriate built-in base, and preserve causes, for example
  `raise DomainError("Useful context") from exc`. Document caller-handled
  domain errors in Google-style `Raises` sections.
  Don't blanket-wrap programming errors or normal iteration termination.

For example, a proposed transfer record can own its positive-amount and
different-account invariants. A raw request adapter checks incoming field
types and required fields before constructing it; an internal caller with typed
arguments uses the constructor's own semantic checks. This is an illustration
of guidance, not an Ataraxia API:

```py
@dataclass(frozen=True)
class Transfer:
    owner_id: str
    recipient_id: str
    cents: int

    def __post_init__(self) -> None:
        if not self.owner_id or not self.recipient_id:
            raise ValueError("account IDs must not be empty")
        if self.owner_id == self.recipient_id:
            raise ValueError("transfer accounts must differ")
        if isinstance(self.cents, bool) or self.cents <= 0:
            raise ValueError("cents must be a positive integer")
```

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
- Keep unavoidable untyped input at the external boundary, following
  [boundary and construction guidance](#validate-at-boundaries-and-construction).
  Do not expose that uncertainty through public result types. Casts,
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
