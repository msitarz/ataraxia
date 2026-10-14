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
exact six-term check and owns guidance/enforcement; this Work owns the separate
question of variant-specific fields, invariants and typed handling.

Compare a union of frozen dataclass variants, a tagged TypedDict union and the
existing flat record. Model shared ownership/identity separately from lifecycle
variants where it clarifies responsibility; avoid duplicating shared fields or
inventing lifecycle rules. `match` selection alone is not an algebraic type
model. [Match selection](../match-selection/README.md) already owns suitable
single-value branching; [literal selection](../literal-selection/README.md)
owns finite string domains and Literal versus Enum. Neither closes the gap in
state-specific field relationships. These Works and
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
values; a type annotation does not establish nonnegativity. Compare the dense
identity check with this illustrative scalar validation, and consider whether
ordinary sequential `if` guards are clearer:

```python
def nonnegative_identity_part(value: object, path: Path) -> int:
    match value:
        case bool():
            raise ValueError(f"malformed sandbox destination identity: {path}")
        case int() as number if number >= 0:
            return number
        case _:
            raise ValueError(f"malformed sandbox destination identity: {path}")
```

Validate untyped input once before exposing a truthful typed domain. Compare
callers, construction, mutation/update needs and JSON roundtrips, retaining
missing/wrong-type/Boolean/negative rejection, original error messages/causes,
diagnostic presence semantics and arbitrary valid extensions. Do not move dense
Boolean conditions into match guards. Python `match` is not inherently
exhaustive: verify narrowing and missing-variant rejection using `assert_never`
or another supported mechanism under locked Pyrefly (1.3.1 at planning baseline
`cd3cb5e6a7abfbb91533c1b14be37b26ff05927a`). Observed checker behavior remains
unknown; do not use casts, broad types or suppression to claim completeness.

- **AC-1 TODO** A short reviewable comparison recommends whether and where a
  variant model improves the seed, comparing dataclass unions, tagged TypedDict
  unions and retained flat records. It explains product versus sum data, typed
  exhaustive handling, simple guards and boundaries where independent `if`
  validation remains clearer; checked evidence and uncertainty are distinct.

  Validation: independently review compact before/after models, affected
  deserialization/typed-consumer/serialization interfaces and candidate
  tradeoffs against the frozen seed and existing engineering/type contracts. Run
  bounded typing/runtime examples through Make during execution, showing useful
  narrowing, missing-variant diagnostics, valid roundtrips and
  malformed-input/extension compatibility. Preserve one-time tool probe results
  under test ownership; recommend a concrete later adoption scope only if
  justified. Run documentation and acceptance checks; split before the
  comparison exceeds a short sitting.
