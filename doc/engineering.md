# Engineering conventions

Read this file when changing or reviewing code or tests. Use
[CONTRIBUTING.md](../CONTRIBUTING.md#make-targets) for validation procedure and
[architecture](architecture.md) for current system contracts.

## Fix the underlying problem

Optimize for the user's complete outcome and maintenance cost across code, tooling,
tests, and docs.

- Trace the cause before adding instructions, exceptions, duplication, or workarounds;
  fix it in the responsible component when possible. Existing behavior is evidence, not
  automatically the intended contract: resolve mismatches against the task and accepted
  decisions.
- Prefer one authoritative implementation or definition; other paths call, derive from,
  or link to it. Automate deterministic steps, such as running all required checks
  through `make ci` and validating invariants at their owning boundary.
- Make the smallest cohesive fix within scope. Preserve intentional differences and
  compatibility; avoid speculative abstractions and unrelated refactors. Explain any
  necessary workaround and its remaining limitation.
- **Revert fundamentally wrong approaches before reimplementing.** If your change
  violates an established contract or convention, revert it and compensating changes,
  including unnecessary supporting code and docs. Preserve unrelated work. Reimplement
  from the restored baseline using project conventions, then validate. Use a targeted
  fix for an isolated defect in an otherwise sound design.
- Update affected callers, tests, and docs together. Verify the actual command, API, or
  user flow, including failures. Do not weaken tests or documented expectations to
  accommodate defects, or leave the user compensating manually.

## Code style

[Ruff configuration](../pyproject.toml) owns formatting, imports, and docstring
checks; [EditorConfig](../.editorconfig) owns file whitespace and encoding.
Use `snake_case` functions/modules and `PascalCase` classes. Satisfy strict
Pyrefly and add `# SPDX-License-Identifier: Apache-2.0` to new source files.

- Prefer function composition, focused functions, guard clauses, and early returns.
  Roughly 25 executable lines is a review signal; extract cohesive helpers that improve
  readability.
- Inject dependencies through arguments or constructor/dataclass fields. Tests use the
  same points with small fakes/stubs. Only if injection is impractical and patching
  necessary, use scoped `unittest.mock.patch`, never pytest's `monkeypatch` fixture.
- Depend on structural `typing.Protocol` contracts for collaborators; value
  objects/internal helpers need not have protocols. Use `@runtime_checkable` for runtime
  checks; see `compute/protocol.py` and `provider.py` under `src/ataraxia/`.
- Model records with dataclasses; prefer `frozen=True` for values and node
  specifications, and `field(default_factory=...)` for per-instance
  containers/collaborators. Keep specifications hashable and execution state in runners;
  see `source.py` and `feature.py`.
- For dictionary records, use `TypedDict` (`BrokerReturn`, `BacktestShardReturn`);
  reserve typed `Mapping[K, V]`/`MutableMapping[K, V]` for dynamic keys such as nodes or
  dependency names.
- At library boundaries, translate expected low-level failures into contextual
  exceptions in `src/ataraxia/errors.py`. Derive from `AtaraxiaError`, retain an
  appropriate built-in base, and preserve causes: `raise DomainError("Useful context")
  from exc` (see `sort_graph`). Don't blanket-wrap programming errors or normal
  iteration termination. Document caller-handled domain errors in Google-style `Raises`
  sections.
- Node pattern: `deps()` names inputs, `factory()` supplies a runner, and runner
  `__call__` computes. Match dependency keys to runner parameters. Extract reusable
  calculations, as `SmaRunner` does with `sma`.
- Use modern typing: `T | None`, built-in generics, `type` aliases, parameterized
  protocols/classes, and `Literal` for closed sets (signal sides). Prefer
  `collections.abc` contracts (`Sequence`, `Mapping`, `Iterator`); require mutability
  only when needed.
- Use context managers for files/providers, preserving source/provider lifecycle
  delegation and cleanup on success/failure; use `pathlib.Path`.
- Keep console output in `src/ataraxia/cli.py`; libraries return values or raise domain
  errors.

### Structural review

Before presenting a change, inspect whether new types and helpers fit the
responsibilities of the surrounding code. Combine similar records only when
their meanings, invariants, and supported operations match. When distinct
record variants repeat fields with the same meaning and compatible types,
consider a shared base (such as a base `TypedDict`) for those fields while
keeping their discriminators and variant-specific contracts separate. Do not
force fields with different meanings or types into the base, or weaken type
precision to remove duplication.

Put a helper with the responsibility it serves; use a shared module only when
its behavior is genuinely shared across owners. Do not move a helper to a
generic utility module merely because its current location is awkward.

Record the structural decision in the step review, including when no refactor is
needed. Keep any refactor within the approved outcome, preserve behavior and
type guarantees, and run the affected checks. A consequential boundary or
contract change returns to the applicable review gate.

### Preserve type precision

Type precision is part of correctness. Passing strict Pyrefly is necessary, but does not
justify losing information about values or their relationships.

- Never resolve a mismatch by widening a meaningful type to `Any`, `object`, an
  unparameterized container, or a base type that discards the required contract. Do not
  remove annotations or add catch-all union members to make incompatible values fit.
  Existing broad types are debt, not precedent for spreading them.
- Introduce types or explicit unions of supported variants as needed to model the
  contract. Preserve input/output relationships with type parameters through producers,
  runners, consumers, and containers. A type parameter must be determined by a typed
  input or owning instance; an unconstrained return-only parameter does not establish
  safety.
- When annotations and behavior disagree, determine the intended supported cases and
  update the affected call chain coherently. Do not retain a false narrow annotation,
  silently drop supported behavior, or substitute a broad return type followed by
  caller-side runtime checks. Creating an appropriate type or separating distinct
  operations is preferable to erasing the distinction.
- Keep unavoidable untyped input at the external boundary. Validate or adapt it there
  into an explicit project contract before it enters application code. Do not expose
  that uncertainty through public result types. Casts, `TypeGuard`/`TypeIs`, ignores,
  and disabled diagnostics must not conceal a mismatch or replace a missing type model;
  narrowing predicates must actually establish their claimed contract.
- Verify both behavior and static guarantees. Run strict Pyrefly and inspect the
  affected signatures and inferred types; for generic or variant contracts, add focused
  type-checking cases that demonstrate precise results and rejection of invalid uses.
  Runtime tests and a green checker alone do not prove that useful type information was
  preserved.

## Testing guidelines

Use pytest, `test_*.py` files, and `test_*` functions. Unit tests precede implementation
and run in isolation; integration tests exercise components across boundaries;
acceptance tests exercise the real user flow. Mirror source modules within
unit/integration/acceptance directories where practical. Use fixtures for reusable
inputs, `pytest.raises` for failures, `tmp_path` for filesystem tests, and `capsys` for
CLI output. Cover changed behavior and relevant edges; meet the branch coverage
threshold configured in [pyproject.toml](../pyproject.toml).

For relevant changes, cover dependency sharing and runner state; provider cleanup on
exhaustion, error, and explicit generator closure; rolling-window ordering/warm-up; and
broker timing preventing same-bar exits for new positions. Use integration tests for
real strategy loading and acceptance tests for CLI output/artifacts.

Run focused tests during development, for example
`uv run pytest test/unit/test_feature.py`. Follow [CONTRIBUTING.md](../CONTRIBUTING.md#make-targets)
for full checks.
