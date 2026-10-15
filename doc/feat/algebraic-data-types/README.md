# Algebraic data type investigation

## Purpose

Determine whether Python variant models and structural `match` with simple
guards make validated lifecycle states clearer and exclude invalid combinations.

## Goals

- Recommend whether and where a variant model improves the sandbox lifecycle
  seed.
- Compare representation, complete record construction, typed decisions, and
  serialization through small illustrative examples.
- Distinguish observed runtime and checker behavior from remaining uncertainty.

## Glossary

- **Algebraic data type:** uses the
  [shared meaning](../../ubiquitous-language.md).

## Non-Goals

- Adopt a dependency, framework, parser, or repository-wide rewrite.
- Replace the guidance and enforcement owned by the
  [condition complexity Work](../conditional-complexity/README.md).
- Adopt the general engineering guidance owned by the
  [validated core guidance Work](../validated-core/README.md).
- Change lifecycle rules, the seed's observable contract, or live resource
  safety requirements.

## Mechanisms

- Frozen dataclass unions, tagged TypedDict unions, and the existing flat record
  are the representation candidates.
- Structural `match` with simple guards illustrates typed variant handling;
  selection alone does not establish an algebraic type model.
- Focused constructors or `__post_init__` establish consumed-field and
  cross-field invariants at the complete record boundary.
- Locked Pyrefly and bounded runtime examples provide evidence about the
  candidates through existing Make targets.

## Visuals

The frozen
[SandboxRecord and Marker at 47779e4](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L38-L92)
use a Literal state and optional diagnostics, with relationships enforced by
[`_validate_record`](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L465-L550).
All four diagnostic strings are required for `failed`, while diagnostic fields
are forbidden for `preparing` and `ready`; destination device/inode are product
data requiring two nonnegative integers that exclude Boolean values.

The reduced proposal below expresses lifecycle as a sum, with separate product
records for shared marker fields and four-string diagnostics; it is illustrative
rather than current or approved code.

```python
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

## Acceptance criteria

### **AC-1 TODO** Representation recommendation

A short comparison recommends whether and where a variant model improves the
seed.

- Frozen dataclass unions, tagged TypedDict unions, and retained flat records
  each have an assessment of fit, pros, cons, and remaining uncertainty.
- Compact before/after models explain product versus sum data, variant-specific
  fields, state-specific relationships, and typed exhaustive handling.
- The comparison assesses candidate compatibility with the frozen seed and
  existing [engineering/type contracts](../../engineering.md).
- The comparison considers callers, construction, mutation/update needs,
  immutable field ownership, and JSON roundtrips rather than treating frozen
  declarations as proof of immutable values.
- Shared ownership/identity is modeled separately from lifecycle variants where
  that clarifies responsibility, without duplicating shared fields or inventing
  lifecycle rules.
- Simple guards and boundaries where independent `if` validation remains clearer
  are identified without moving dense Boolean conditions into match guards.
- Checked evidence is distinguished from assumptions, and a concrete later
  adoption scope is recommended only if justified.

### **AC-2 TODO** Complete boundary and compatibility comparison

The examples show each candidate across the complete consumed-record boundary.

External parsing, complete record construction, a pure typed decision such as
`failure_details(state: Lifecycle) -> FailureDiagnostics | None`, and
serialization have distinct responsibilities and interfaces under the
[validated core boundary rules](../validated-core/README.md#acceptance-criteria).

- Complete consumed-field and cross-field validation precedes pure typed
  decisions, including truthful validated product inputs/results and lifecycle
  variants rather than isolated scalar checks alone.
- Ownership, persistence, and security fields remain consumed, including
  generation, schema, owner, and destination device/inode even when the pure
  decision does not read them.
- Missing, wrong-type, Boolean, and negative values retain their rejection,
  alongside relevant documented errors/causes and diagnostic presence semantics.
- Serialization preserves the seed's schema and valid JSON-compatible extension
  fields as opaque data under required transport/persistence compatibility,
  without speculative validation of unused external schema.
- Pure decisions use valid typed values without raw representations, repeated
  defensive type checks, filesystem/process probes, or effectful ports, while
  permitting typed path/location values and pure transformations under their
  declared input/output contract.
- Bounded runtime examples run through Make show valid roundtrips, whole-record
  invalid-field and cross-field cases, and extension compatibility.

Model invariants and live resource safety remain distinct in the comparison.
Mutable filesystem generation/inode and held-lock freshness still require
effectful adapter checks under lock at the lifecycle's required points; frozen
records do not replace fail-closed checks against changes between checking and
use. Resource revalidation evidence stays at its effectful adapter/lifecycle
boundary, separately from pure-rule examples.

### **AC-3 TODO** Observed typing guarantees and limits

Bounded typing examples establish what the locked checker supports for the
candidate representations.

- Examples run through Make show useful narrowing and missing-variant
  diagnostics using `assert_never` or another supported mechanism.
- Findings explain that Python `match` is not inherently exhaustive and do not
  use casts, broad types, or suppressions to claim completeness.
- Findings distinguish static handling from runtime invariants, including that
  `int()` class patterns accept Boolean values and annotations or `frozen=True`
  do not establish runtime field types or nonnegativity.
- One-time probe methods and observed results are retained under
  [test ownership](../../test-ownership.md) rather than treated as ongoing
  regression coverage.

#### What exists

Pyrefly is locked at 1.3.1 at planning baseline
`cd3cb5e6a7abfbb91533c1b14be37b26ff05927a`; narrowing and missing-variant
behavior have not yet been observed for these examples.

## Dependencies

There is no prerequisite Work for the comparison. The
[validated core guidance Work](../validated-core/README.md) owns general
validation, immutable values, pure rules, and adapter boundaries; this
Investigation applies its proposed direction independently and reconciles its
recommendation with adopted guidance before any later adoption.

## Links

- [PR #328 complexity comment](https://github.com/msitarz/ataraxia/pull/328#discussion_r4272687628):
  the seed for this separate representation question; the PR remains independent
  and execution inspects then-integrated source.
- [Condition complexity Work](../conditional-complexity/README.md): owns
  guidance/enforcement and the seed's observable input/error/safety contract,
  permitting validation order and branch organization to change.
- [Selection and nested-exception guidance](../../engineering.md#code-style)
  and
  [finite-string-domain guidance](../../engineering.md#preserve-type-precision):
  delivered guidance for single-value branching, nested exceptions, Literal, and
  domain ownership, related to this Investigation without merge dependencies.

## Additional context

The delivery is a bounded recommendation and small illustrative examples that
fit a short review sitting. Any production adoption requires a later concrete
Work; this Investigation does not establish production readiness or resolve the
representation choice in advance.
