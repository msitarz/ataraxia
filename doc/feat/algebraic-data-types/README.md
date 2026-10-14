# Algebraic data type investigation

Investigate whether Python variant models and structural `match` with simple
guards make validated lifecycle states clearer and exclude invalid combinations.
This bounded Investigation produces a recommendation and small illustrative
examples; it does not adopt a dependency, framework, parser or repository-wide
rewrite. Use the [glossary meaning](../../ubiquitous-language.md) of algebraic
data types. A later concrete adoption Work is required if justified.

The seed is the maintainer's
[complexity comment on PR #328](https://github.com/msitarz/ataraxia/pull/328#discussion_r4272687628)
and frozen
[`_validate_record` at reviewed head 47779e4](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L465-L550).
The
[flat SandboxRecord and Marker](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L38-L92)
use a Literal state and optional diagnostics; runtime validation requires all
four diagnostic strings for `failed` and forbids diagnostic fields for
`preparing`/`ready`. Destination device/inode form product data: both values are
required nonnegative integers excluding Boolean values. The
[condition complexity Work](../conditional-complexity/README.md) preserves the
observable input/error/safety contract and owns guidance/enforcement; it permits
validation order and branch organization to change. This Work owns the separate
question of variant-specific fields, invariants and typed handling.

Compare a union of frozen dataclass variants, a tagged TypedDict union and the
existing flat record. Model shared ownership/identity separately from lifecycle
variants where it clarifies responsibility; avoid duplicating shared fields or
inventing lifecycle rules. `match` selection alone is not an algebraic type
model. The delivered [selection guidance](../../engineering.md#code-style) owns
the separate question of suitable single-value branching; the delivered
[finite-string-domain guidance](../../engineering.md#preserve-type-precision)
records the recommendation for Literal and domain ownership. That
concern is separate from this Work's variant-specific fields and state-specific
field relationships. These Works and
[nested exceptions](../nested-exceptions/README.md) are related, not merge
dependencies. PR #328 remains independent; inspect then-integrated source when
executing this Investigation.

The following reduced illustration shows a proposed sum of lifecycle variants,
not current or approved code. Shared marker fields and four-string diagnostics
would have their own product records; serialization must still preserve the
seed's schema and JSON-compatible extension fields.

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

Boundary validation is still required. A class pattern `int()` accepts Boolean
values; annotations and `frozen=True` do not establish nonnegativity or runtime
field types. Compare candidates at a complete consumed-record boundary,
constructing truthful validated product inputs/results and lifecycle sum
variants. Focused constructors or `__post_init__` must enforce consumed fields
and cross-field invariants, including diagnostics associated with the state.
Simple sequential guards may be clearer inside that boundary; isolated scalar
helpers alone do not establish record validity.

The [validated core guidance Work](../validated-core/README.md) owns the general
engineering outcome, including complete validation that permits fail-fast
errors and validated construction of new results/state transitions without
mutation or bypass. This Investigation applies that proposed direction when
comparing representations; it may proceed independently and must reconcile its
recommendation with the adopted guidance before any later adoption. Illustrate
external parsing, complete record construction, a typed pure decision such as
`failure_details(state: Lifecycle) -> FailureDiagnostics | None`, and
serialization as distinct responsibilities. Pure decisions consume validated
domain values without raw/unvalidated representations, repeated defensive type
checks or filesystem/process probes. Typed path/location values and pure
transformations of them are permitted under the declared input/output contract.
A decision invoking
an effectful port is not pure. Compare immutable field ownership as well as
frozen dataclass declarations; frozen records containing mutable containers do
not establish immutable values.

Validate a complete consumed record once per boundary crossing. Fields needed
for ownership, persistence or security remain consumed even if a pure decision
does not read them: generation, schema, owner and destination device/inode
cannot be dropped. Preserve unrelated extensions as opaque data subject to
required transport/persistence compatibility; avoid speculative validation of
unused external schema. Compare callers, construction, mutation/update needs and
JSON roundtrips, retaining missing/wrong-type/Boolean/negative rejection,
relevant documented errors/causes, diagnostic presence semantics and valid
extensions. Mutable filesystem generation/inode and held-lock freshness still
require effectful adapter checks under lock at the lifecycle's required points;
a frozen record cannot ensure live resource safety or replace fail-closed TOCTOU
checks. Do not move dense Boolean conditions into match guards. Python `match`
is not inherently exhaustive: verify narrowing and missing-variant rejection
using `assert_never` or another supported mechanism under locked Pyrefly (1.3.1
at planning baseline `cd3cb5e6a7abfbb91533c1b14be37b26ff05927a`). Observed
checker behavior remains unknown; do not use casts, broad types or suppression
to claim completeness.

- **AC-1 TODO** A short reviewable comparison recommends whether and where a
  variant model improves the seed, comparing dataclass unions, tagged TypedDict
  unions and retained flat records. It explains product versus sum data, typed
  exhaustive handling, simple guards and boundaries where independent `if`
  validation remains clearer. Complete consumed-record validation precedes pure
  typed decisions and preserves ownership/persistence/security fields and opaque
  extensions; checked evidence and uncertainty are distinct.

  Validation: independently review compact before/after models, affected
  deserialization/typed-consumer/serialization interfaces and candidate
  tradeoffs against the frozen seed and existing engineering/type contracts. Run
  bounded typing/runtime examples through Make during execution, showing useful
  narrowing, missing-variant diagnostics, valid roundtrips and whole-record
  invalid-field/cross-field cases and extension compatibility. Review live
  resource revalidation separately from model invariants. Pure-rule examples use
  valid typed values; adapter/lifecycle evidence stays at its owning effectful
  boundary. Preserve one-time tool probe results under test ownership; recommend
  a concrete later adoption scope only if justified. Run documentation and
  acceptance checks; split before the comparison exceeds a short sitting.
