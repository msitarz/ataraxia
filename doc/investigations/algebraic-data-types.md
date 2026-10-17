# Algebraic data type investigation findings

This report records the completed bounded comparison defined by the
[Algebraic data type Investigation contract](https://github.com/msitarz/ataraxia/blob/48ddb9e/doc/feat/algebraic-data-types/README.md).
It did not change production code or adopt a repository-wide representation
rule.

## Scope and recommendation

The comparison uses the sandbox marker and validator pinned at
[47779e4](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py).
The checkout at this report's base has since moved on; the code examples and
probe model that historical marker contract, not current `script/sandbox.py`.

The three candidates share one complete external boundary and preserve the same
JSON shape. The flat `TypedDict` remains the best persistence and incremental
update representation for that seed. A dataclass lifecycle union is useful
after validation when a pure internal decision benefits from required
variant-specific fields. A tagged `TypedDict` union can make the mapping's
variant shape visible to typed callers, but keeps mutable mapping ownership and
does not validate runtime input. This is a recommendation for this marker's
boundary and possible internal decision; it does not authorize production
adoption.

| Candidate | Before / after model | Callers, updates, ownership, and JSON | Remaining uncertainty |
| --- | --- | --- | --- |
| Flat `TypedDict` | Before and after: one `state: Literal[...]` with four `NotRequired[str]` diagnostic keys. Complete validation leaves the state/diagnostic relationship as a runtime invariant. | Persistence serializes the mapping directly. `SandboxChanges` applies a mutable patch while the marker lock is held, then revalidates the complete merged record. Extensions are separately owned by `Marker`; serialization flattens `extensions | owned`. | Consumers see diagnostics as optional for every state. A narrowed state does not encode required diagnostics. |
| Tagged `TypedDict` union | Before: the flat mapping. After: `PreparingRecord`, `ReadyRecord`, and `FailedRecord`; each has the shared product fields, while `FailedRecord` requires all four diagnostic strings. | The union remains JSON-shaped and can be flattened with opaque extensions. Callers narrow on `record["state"]`. Updates remove incompatible diagnostic keys and construct a new validated variant. `TypedDict` itself does no runtime checking or ownership management. | Pyrefly narrows on the discriminant, but this probe does not establish runtime safety or exactness for arbitrary extra keys. |
| Frozen dataclass union | Before: the flat mapping. After: the marker product owns schema, generation, owner, destination identity, extensions, and one `Lifecycle`; `Failed` owns a `FailureDiagnostics` product. | A validated pure consumer matches required variant data. State changes replace the lifecycle and construct a new marker. An adapter flattens product and variant fields into the seed's JSON keys. `frozen=True` is shallow; extension dicts and nested values need explicit ownership. | No production consumer in this Investigation demonstrates that conversion and replacement are worthwhile. Runtime annotations and freezing do not validate values. |

The concrete shape change is:

```python
# Before: one flat transport record.
class SandboxOwner(TypedDict):
    common_dir: str
    project: str
    base: str


class SandboxRecord(SandboxOwner):
    schema_version: int
    generation: str
    destination_device: int
    destination_inode: int
    state: Literal["preparing", "ready", "failed"]
    failure_stage: NotRequired[str]
    failure_status: NotRequired[str]
    failure_stdout: NotRequired[str]
    failure_stderr: NotRequired[str]


class SharedFields(TypedDict):
    schema_version: int
    generation: str
    common_dir: str
    project: str
    base: str
    destination_device: int
    destination_inode: int


# After, tagged mapping form.
class PreparingRecord(SharedFields):
    state: Literal["preparing"]


class ReadyRecord(SharedFields):
    state: Literal["ready"]


class FailedRecord(SharedFields):
    state: Literal["failed"]
    failure_stage: str
    failure_status: str
    failure_stdout: str
    failure_stderr: str


type TaggedLifecycle = PreparingRecord | ReadyRecord | FailedRecord


# After, dataclass form: common fields stay a product; lifecycle is a sum.
type JsonValue = (
    str | int | float | bool | list[JsonValue] | dict[str, JsonValue] | None
)


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


@dataclass(frozen=True)
class Owner:
    common_dir: str
    project: str
    base: str


@dataclass(frozen=True)
class DestinationIdentity:
    device: int
    inode: int


type Lifecycle = Preparing | Ready | Failed


@dataclass(frozen=True)
class Marker:
    schema_version: int
    generation: str
    owner: Owner
    destination: DestinationIdentity
    lifecycle: Lifecycle
    extensions: dict[str, JsonValue]
```

The product and sum distinction is visible in the dataclass form: owner,
schema, generation, and destination identity are shared product data; lifecycle
is one of three alternatives; diagnostics belong only to the failed
alternative. The full executable model and checker signatures are retained in
the executable probe and its checker expectation file referenced below.

## Exact boundary carried by the examples

The probe follows the pinned `_read_marker` and `_validate_record` behavior.
External JSON decoding translates `OSError`, `JSONDecodeError`, and
`UnicodeDecodeError` into contextual `ValueError` while preserving the original
exception as `__cause__`. Missing files remain a separate `None` result in the
seed's filesystem reader. The bounded probe exercises read-error cause
preservation separately from byte decoding and record validation; it does not
replay the seed's filesystem metadata, symlink, or locking checks.

Complete validation requires a string-keyed object whose values are finite
JSON values; `schema_version` must be integer `1` and cannot be `bool`;
`generation` must be 32 lowercase hexadecimal characters; `common_dir`,
`project`, and `base` must be strings (the seed does not require nonempty
strings); state must be `preparing`, `ready`, or `failed`; destination device
and inode must be nonnegative integers excluding `bool`. On `failed`, all four
diagnostic values must be strings (empty strings are accepted). For every other
state, the presence of any diagnostic key is rejected, even when its value is
`null`. A `null` diagnostic on `failed` is rejected as incomplete. Unknown
string-keyed fields are retained as JSON-compatible extensions. Serialization
restores the owned fields and extensions to the same flattened mapping.

The decision consumes only validated lifecycle data. Schema, generation,
ownership, destination identity, and extensions remain part of construction and
serialization even when that pure decision does not read them. Filesystem
identity and held-lock freshness remain effectful adapter checks; model validity
does not establish current resource safety. Simple state selection can use
`match`; unrelated input constraints remain independent guards rather than a
dense compound guard.

## Probe code and observed results

The one-time executable probe, removed after review, is archived at the
[accepted runtime probe source](https://github.com/msitarz/ataraxia/blob/d39fd1ef3e36ce533b4edfbcc0dc41e1d202c074/test/script/unit/test_adt_investigation_probe.py).
It decodes and validates at the external boundary, then narrows every consumed
field into one `DataclassRecord` product. That record is also the dataclass
candidate, avoiding a duplicate validated model. Flat and tagged adapters
consume it; their complete wrappers validate direct construction through typed
adapters, without serializing and reparsing. The shared product checks typed
dataclass construction, and all three candidates reject extension keys that
shadow owned fields. Serialization places owned fields last, matching the
seed's precedence. The probe performs full JSON roundtrips, checks extension
preservation and state updates, and sends invalid whole records through each
candidate boundary. Its cases cover missing and wrongly typed consumed values,
Boolean and negative destination identity, failed diagnostic gaps,
diagnostic-key presence with `null`, unexpected diagnostics on a non-failed
state, invalid extension data, decode causes, shallow frozen contents, and
`int()` class patterns accepting `bool`.

The one-time type probe, also removed after review, is archived at its
[accepted checker expectation source](https://github.com/msitarz/ataraxia/blob/d39fd1ef3e36ce533b4edfbcc0dc41e1d202c074/test/script/typecheck/algebraic_data_types_probe.py).
It imports the executable candidate types and exercises their construction,
decision, and transition functions in positive `assert_type` checks. Pyrefly
1.3.1 narrows a dataclass union and tagged `TypedDict` union when the
discriminant is matched; omitting only `Failed` causes an observed
`assert_never` diagnostic in each. The probe also checks that tagged narrowing
exposes the required diagnostics and that dataclass decisions return
`FailureDiagnostics | None`. For the flat model, the same
diagnostic catches an omitted state literal, but diagnostics remain optional
after state narrowing. A mapping-pattern match on the entire tagged
`TypedDict` union did not narrow its fields usefully; the probe retains that
unsupported attempt as an expected diagnostic rather than claiming coverage.

Observed through Make on the corrected investigation revision:

- `make test ARGS=test/script/unit/test_adt_investigation_probe.py` — 41
  passed: valid full-record roundtrip, pure decision, and state update for each
  candidate; eight invalid whole-record cases and two parse-cause cases per
  candidate; a read-error cause case; negative-identity and extension-collision
  direct-constructor cases for each candidate; and one runtime freeze/pattern
  case.
- `make typecheck ARGS=test/script/unit/test_adt_investigation_probe.py` —
  passed with zero diagnostics, checking the executable construction path
  itself.
- `make typecheck-expectations ARGS=test/script/typecheck/algebraic_data_types_probe.py`
  — three expected omitted-case diagnostics (flat state, tagged union, dataclass
  union) plus the expected mapping-pattern type error; positive assertions
  against the implementation passed with no unexpected checker errors.
- `make doc-check ARGS=doc/investigations/algebraic-data-types.md` — passed.

These were one-time representation probes, not ongoing regression tests. They
were removed in the separate reviewed cleanup because no production integration
regression tests were added. The report retains their methods and observed
results; the immutable links above preserve the exact reviewed source revision.
