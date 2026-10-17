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
The project requires Python 3.14 or newer and uses native deferred annotation
evaluation; do not add `from __future__ import annotations`.

- Prefer function composition, focused functions, guard clauses, and early
  returns. Ruff's PLR0915 counts statements in source, scripts, and tests:
  26–50 statements are advisory and more than 50 blocks lint. Treat about 25
  statements as a review signal; these counts guide readability review, not
  function shape. Don't split code only to lower a count. Extract cohesive
  helpers that improve readability.
- Inject dependencies through arguments or constructor/dataclass fields.
- Define reusable `typing.Protocol` ports from consumer needs, with precise
  inputs, outputs, documented errors, and lifecycle ownership. Concrete
  adapters satisfy them structurally and are supplied by composition;
  dependencies point toward the consumer's contract, and core imports no
  concrete adapters. Use `@runtime_checkable` only when runtime conformance is
  actually checked. Value objects and internal helpers need no protocol; see
  `compute/protocol.py` and `provider.py` under `src/ataraxia/`.
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
- Use `match` when one stable value selects among mutually exclusive cases;
  preserve supported cases and required unmatched-input behavior. For
  independent constraints, use short guards or separate `if` statements. A
  small local collection of conditions and diagnostics suits cases where
  callers need accumulated findings; keep type prerequisites explicit and
  preserve distinctions callers rely on. A dictionary lookup can suit a simple
  mapping from keys to fixed values, but tables and variants are not mandatory.
  Do not hide dense predicates in guards, comprehensions, or extracted helpers
  merely to lower a metric.
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
from dataclasses import dataclass
from datetime import datetime
from typing import assert_never


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


@dataclass(frozen=True)
class ImmediateTransfer:
    details: Transfer


@dataclass(frozen=True)
class ScheduledTransfer:
    details: Transfer
    execute_at: datetime


type TransferPlan = ImmediateTransfer | ScheduledTransfer


def scheduled_time(plan: TransferPlan) -> datetime | None:
    match plan:
        case ImmediateTransfer():
            return None
        case ScheduledTransfer(execute_at=execute_at):
            return execute_at
        case unexpected:
            assert_never(unexpected)


def schedule(plan: ImmediateTransfer, execute_at: datetime) -> ScheduledTransfer:
    return ScheduledTransfer(details=plan.details, execute_at=execute_at)
```

Fields needed together form a product record; a variant-specific field such as
`execute_at` belongs on its alternative when that makes invalid combinations
harder to express. A flat record remains suitable when its fields fit every
case. Frozen dataclasses are shallow: use immutable containers or document who
owns mutable contents. Represent a state transition by constructing a new
validated result or variant from the prior valid value, rather than mutating a
frozen value or bypassing construction with `object.__setattr__`. Stateful
runners and resource holders keep their explicit mutable ownership.

For a closed union, handle each alternative while preserving type narrowing; a
supported exhaustive helper such as `assert_never` makes a missing case visible
to the type checker. Python `match` alone does not guarantee exhaustive
handling. Do not erase useful variant types with casts, broad types, or
suppressions.

`Transfer("acct-a", "acct-b", 125)` is a valid construction; using
`"acct-a"` for both IDs raises `ValueError`. Calling `schedule` with an
`ImmediateTransfer` constructs a new `ScheduledTransfer` and leaves the input
plan unchanged.

### Pure typed decisions

A pure decision is a pure function over valid typed domain values; its result
is determined by those explicit inputs. It performs no I/O, reads no
environment, clock, random source, or global state, and does not mutate its
arguments. It does not reparse raw input, repeat defensive checks on validated
children, or probe files or processes; validation belongs at the
[owning boundary](#validate-at-boundaries-and-construction). A newly
constructed domain result enforces its own invariants. Calling an effectful
collaborator remains an effect even when its contract is a `typing.Protocol`.

The illustrative `scheduled_time` decision uses only its validated plan and
returns either its explicit schedule or `None`. Separate a substantial
per-item decision from collection traversal and cross-item state when that
clarifies the contract; keep accumulators visible in a loop instead of hiding
them in a comprehension. Prefer standard Python protocols such as iteration
and `collections.abc.Sized` when their semantics fit, and retain named methods
when they express distinct domain meaning.

### Effects and live resource safety belong to adapters

Adapters own effectful operations, expected failure translation, and the
lifecycle of resources they acquire. Normalize untyped inputs once at their
ingress boundary, then reuse the adapted values and observations; rely on a
documented typed API's guarantees instead of repeating them or routinely
preflighting an operation. Follow the existing
[boundary error guidance](#validate-at-boundaries-and-construction) for
context and causes, and the [resource handling conventions](#code-style) for
cleanup on success and failure.

Keep essential current ownership, authorization, lifecycle, and safety checks
at the operation that needs them. Use transactions or synchronization to make
state-dependent checks and writes atomic where required; a valid persisted
record alone does not prove that current access or resource state is safe.
When validation or control flow changes, preserve supported inputs, documented
errors and causes, state invariants, persistence compatibility, and necessary
effect ordering. Incidental check order and defensive branch layout remain
implementation choices.

For example, the consumer-owned transfer port can be backed by a small SQLite
adapter. Ingress adapts raw request fields once into the validated `Transfer`;
the adapter uses those values directly. The authenticated actor ID is checked
at submission time, and the insert is attempted inside a transaction instead
of being preflighted by a separate availability query. A live permission
stored in the database would need an atomic operation-level check as well.
Assume database setup creates the `transfers` table and its constraints. The
composition root supplies
`SQLiteTransferSubmitter(database=Path("transfers.sqlite"))` to
`submit_transfer`; the adapter owns each per-call connection and closes it
after the transaction on success or failure. This is an illustrative adapter,
not an Ataraxia API:

```py
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from typing import Protocol
from uuid import uuid4


class SubmissionError(Exception):
    """Expected failure reported when a transfer cannot be submitted."""


@dataclass(frozen=True)
class Receipt:
    reference: str


class TransferSubmitter(Protocol):
    """Consumer-owned transfer submission contract.

    Raises:
        PermissionError: The authenticated actor does not own the transfer.
        SubmissionError: The adapter cannot submit the transfer.
    """

    def submit(self, actor_id: str, transfer: Transfer, /) -> Receipt: ...


@dataclass(frozen=True)
class SQLiteTransferSubmitter:
    database: Path

    def submit(self, actor_id: str, transfer: Transfer, /) -> Receipt:
        if actor_id != transfer.owner_id:
            raise PermissionError("actor does not own this transfer")
        reference = uuid4().hex
        try:
            with closing(sqlite3.connect(self.database)) as connection, connection:
                connection.execute(
                    "INSERT INTO transfers "
                    "(reference, owner_id, recipient_id, cents) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        reference,
                        transfer.owner_id,
                        transfer.recipient_id,
                        transfer.cents,
                    ),
                )
        except (sqlite3.IntegrityError, sqlite3.OperationalError) as exc:
            raise SubmissionError("The ledger operation failed") from exc
        return Receipt(reference=reference)


def submit_transfer(
    actor_id: str, transfer: Transfer, submitter: TransferSubmitter
) -> Receipt:
    return submitter.submit(actor_id, transfer)
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
