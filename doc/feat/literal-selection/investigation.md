# Literal selection investigation

## Finding and recommendation

Use `Literal` for a small finite set of string values when callers benefit from
static rejection of unsupported names. Keep request, configuration, plugin,
path, hash, and other open external strings typed as `str` until the owning
boundary validates them; return the narrow type only after validation. Preserve
the validator's runtime rejection. Match arms, current test parameters, or
observed values alone do not establish that an input domain is closed.

The historical example has two distinct domains: five changed-input names
(`declaration`, `evidence`, `file`, `link`, `record`) and eight record names
(`accepted`, `uv`, `index`, `platform`, `layout`, `metadata`, `undeclared`,
`version`). A path and a digest remain open `Path` and `str` values. At
[`4030819`](https://github.com/msitarz/ataraxia/blob/403081936833e579384d138aa0da43517ba6d09c/test/script/selection_inputs.py#L28),
both `copy_selection_fixture(..., record_name: str)` and
`arrange_changed_input(..., change: str)` receive strings; fixture callers
pass `parameter_name(request)`, which first checks that pytest's untyped
`request.param` is a string. The later
[`63d2a7b` narrowing change](https://github.com/msitarz/ataraxia/commit/63d2a7b)
adds separate `RecordName` and `ChangedInput` aliases, boundary validators,
and rejection cases. The reviewed `5d37d04` source already contains that
adoption. This corrects the seed provenance in the Work README.

For domains this small, prefer a named `Literal` alias when consumers need
static precision and ordinary strings remain the useful runtime representation.
The consumer annotation does not validate runtime data. There are two feasible
ways to keep the static and runtime domains aligned:

- An explicit `match` in `changed_input_name(value: str) -> ChangedInput` is
  direct and readable when cases have distinct actions. It repeats each string
  in the alias and match. Pyrefly checks that returned values fit the alias,
  but cannot prove that the match accepts every alias member; an omitted member
  will be rejected at runtime even though its type is allowed.
- A metadata-backed predicate can make the alias the single value inventory:

  ```python
  type ChangedInput = Literal[
      "declaration", "evidence", "file", "link", "record"
  ]

  def is_changed_input(value: str) -> TypeIs[ChangedInput]:
      return value in get_args(ChangedInput.__value__)
  ```

  The runtime membership check reads the Literal arguments from the PEP 695
  alias; the predicate narrows a validated `str` without a cast. Python 3.14
  exposes
  [`TypeAliasType.__value__` and `get_args`](https://docs.python.org/3.14/library/typing.html#typing.TypeAliasType),
  and [`TypeIs`](https://docs.python.org/3.14/library/typing.html#typing.TypeIs)
  tells the checker how a true result narrows the string. The probe files below
  confirm this works with pinned Pyrefly. `TypeIs` is still a soundness promise:
  the checker does not prove an arbitrary predicate correct. Here the return
  value is literally the membership test against the alias metadata, and the
  runtime probe checks supported values, values from the other domain, and
  unknown inputs. Use one named predicate per domain so the five-name and
  eight-name inventories remain distinct.

Prefer the metadata-backed predicate when a plain string domain needs one
authoritative inventory and the alias is a flat `Literal`. Prefer explicit
matched narrowing when separate cases do distinct work and that clarity
outweighs repeating the values; tests must then cover every supported member
and unsupported values. Do not add a parallel set or registry in either
approach. An `Enum` is another single runtime inventory when named identity or
behavior is useful: constructing `Kind(value)` validates and returns a member
or raises `ValueError`, but consumers now use enum members and wire strings
must be converted at the boundary. It adds ceremony when selectors only route
strings.

Keep `str` when values are open, forwarded unchanged, or intentionally
future-compatible. An intentional default such as `case _: return "text"`
accepts future values; that is not an accidentally incomplete finite domain.

Do not flag these as closed domains based only on matches: an open `str` may
have a meaningful fallback; a path or plugin key may have an unbounded set of
values; overlapping predicates such as prefixes and exact names may classify
the same string; a future format or record extension can make a currently
complete-looking arm set intentionally extensible. A false positive can erase
accepted behavior or add inappropriate rejection. Preserve the original open
type and default unless an independently owned contract establishes a finite
boundary.

## Tooling evidence

The assigned environment used Python 3.14.8, Pyrefly 1.3.1, and Ruff 0.16.8;
the latter two match `uv.lock`. The exact executed sources are retained as
small linked Work probes through evidence review: the explicit-match type case
([type probe](../../../test/ataraxia/typecheck/literal_selection_probe.py)),
open versus closed match
([exhaustiveness probe](../../../test/ataraxia/typecheck/literal_exhaustiveness_probe.py)),
alias-backed `TypeIs` positive and negative types
([inventory type probe](../../../test/ataraxia/typecheck/literal_selection_inventory_probe.py)),
runtime implementations
([inventory probe module](../../../test/script/literal_selection_inventory_probe.py)),
and runtime cases
([explicit-match cases](../../../test/script/unit/test_literal_selection_probe.py),
[single-inventory cases](../../../test/script/unit/test_literal_selection_inventory_probe.py)).
The isolated type-predicate probe uses a separate two-value toy alias; the
runtime probe keeps each historical five-name/eight-name alias as its sole
literal inventory.

- `make typecheck-expectations ARGS=test/ataraxia/typecheck/literal_selection_probe.py`
  and
  `make typecheck-expectations ARGS=test/ataraxia/typecheck/literal_selection_inventory_probe.py`
  both exited 0. The first emitted the expected `bad-argument-type` (“Argument
  `str` is not assignable”) and `bad-return` (“Returned type
  `Literal['future-option']` is not assignable”) diagnostics, then
  `INFO 2 errors`. The second emitted the expected `bad-argument-type` for an
  open string and `INFO 1 error`; its positive branch verifies `TypeIs`
  narrowing.
- `make typecheck ARGS=test/script/literal_selection_inventory_probe.py`,
  `make typecheck ARGS=test/script/unit/test_literal_selection_inventory_probe.py`,
  and `make typecheck ARGS=test/script/unit/test_literal_selection_probe.py`
  each exited 0 with `0 errors`.
- `make typecheck ARGS=test/ataraxia/typecheck/literal_exhaustiveness_probe.py`
  exited successfully and reported `0 errors (1 warning not shown)` for a
  missing arm over `Literal[...]`. The matching open-`str` example added no
  warning. The configured Make output therefore does not expose this warning
  as an actionable gate. Pyrefly documents a `non-exhaustive-match` warning for
  closed types and says `non-exhaustive-match-open-type` is ignored by default
  ([error kinds](https://pyrefly.org/en/docs/error-kinds/#non-exhaustive-match)).
  This operates on an already declared closed type; it does not find candidate
  domains in arbitrary string matches.
- `make lint-check ARGS='test/ataraxia/typecheck/literal_selection_probe.py test/ataraxia/typecheck/literal_exhaustiveness_probe.py test/ataraxia/typecheck/literal_selection_inventory_probe.py test/script/literal_selection_inventory_probe.py test/script/unit/test_literal_selection_probe.py test/script/unit/test_literal_selection_inventory_probe.py'`
  exited 0 with “All checks passed!” and no domain-finding diagnostic. Ruff's
  configured lint run gives no signal about whether a string domain is closed.
  Its rules cover syntax and maintainability patterns, not project-specific
  domain intent ([Ruff rules](https://docs.astral.sh/ruff/rules/)).
- `make test ARGS='test/script/unit/test_literal_selection_probe.py test/script/unit/test_literal_selection_inventory_probe.py'`
  exited 0 with 15 passed. Cases exercise explicit narrowing and rejection, an
  open-string fallback that accepts a future value, Enum identity, and
  alias-backed runtime membership for both distinct domains, including an
  unsupported cross-domain name and unknown values.

Pyright and mypy offer alternative exhaustiveness diagnostics for typed
`Literal`/Enum domains: Pyright's `reportMatchNotExhaustive` defaults to
`none`, and mypy's `exhaustive-match` error code is opt-in
([Pyright configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md#reportmatchnotexhaustive),
[mypy Literal types](https://mypy.readthedocs.io/en/stable/literal_types.html#exhaustiveness-checking)).
These checks likewise need an explicitly closed subject type. Neither they nor
the pinned tools establish domain closure merely from matching strings.
Switching type checkers or adding a heuristic linter would not solve that
intent problem; a detector would need dataflow and policy for defaults,
extensions, dynamic registries, and overlapping predicates, with substantial
false-positive risk.
The Pyright and mypy comparison is documentation-only; neither tool was
installed or executed in this Work.

## Follow-up

A small guidance adoption Work is warranted. It should update the existing
[`Literal` and type-precision guidance](../../engineering.md#preserve-type-precision)
to state the boundary rule, retain runtime rejection, explain when plain `str`
is intentionally open, and reserve Enum for useful identity or behavior. It
should include the open-default and dynamic-domain counterexamples. Do not add
a general lint rule, checker migration, automatic str-to-Literal rewrite, or
policy that every match must be exhaustive. This report records the
investigation; the follow-up Work should promote only the reviewed guidance to
its authoritative owner.
