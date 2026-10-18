# Engineering judgment in review

Read this when changing or reviewing code or tests. Apply these questions as
you make small changes and when you review the completed result. Review the
affected responsibility across its consumers, including relevant unchanged
code; assess duplication in meaning, ownership, and interpretation as well as
source text.

- Does the change implement the Work's smallest coherent design?
- Before adding a parser, validator, type, or filesystem behavior, were
  adjacent consumers of the same domain concepts inspected? Does shared
  meaning have a common domain owner, with existing callers migrated together?
  Would a rule change otherwise require multiple parsers, validators, or status
  inventories?
- Can repeated state and interpretation be derived from one representation
  that retains the information consumers need, including for diagnostics?
- Do types with the same meaning belong together? Does shared code have a
  named responsibility without depending on sibling consumer internals, while
  consumer-specific selection, orchestration, diagnostic presentation,
  effects, and intentional contract differences stay at their owners?
- For distinct variants with shared fields or behavior, would a shared base or
  helper clarify their common contract, including for diagnostics?
- Do checks and abstractions earn their complexity?
- Are shared rules tested at their owner and distinct behavior tested at
  consumer entry points? Do types, behavior, tests, and effects live with
  their owning responsibility?

Keep intentional overlap when it is clearer and explain it in the PR. Move code
or extract a helper only when that clarifies its responsibility and resulting
contract. Review may accept the design unchanged; no refactor or comment quota
applies.

## Three contrasts

These examples distinguish accepted history from possible future choices.
They illustrate judgment; they do not require rewriting similar code.

### Use standard Python semantics

**Historical changes** (`1d43b18`, `d01a316`): before, `TextBlock` repeated a
set of literal kinds and `SourceLocation` exposed `.contains(child)`; after,
the current [Markdown model](../script/markdown/model.py) derives literal kinds
from `TextKind` and expresses range membership as `child in parent`. This
removes a second inventory and uses Python's membership protocol. Keep a named
operation when its domain meaning differs from ordinary membership.

### Select one case or collect independent findings

**Historical changes** (`1417db3`, `561816e`): before, Work selection used
separate file-kind checks; the current
[discovery code](../script/work/source.py) uses `match` because a path
has one mode. The current [Work rules](../script/work/contract.py) instead
collect independent criterion failures so one malformed declaration can report
more than one finding. Checks that need parsed fields remain behind a successful
format match. Use exclusive dispatch for one-of-many cases; use clear guards or
a small local collection when independent constraints can accumulate. Keep
prerequisites visible and predicates readable.

### Attempt the operation and handle its expected failure

**Historical change** (`fedb722`): Work discovery removed a separate symlink
probe and local resolver wrapper; its current owner resolves the selection and
translates expected filesystem errors, while contract reads translate failures
at the read site. A possible future adapter can likewise attempt a read or
write and handle its expected failure where that operation is owned. Preserve
root containment, authorization, ownership, and resource lifecycle checks that
the operation alone cannot establish; state-dependent checks may need to be
atomic with the operation.

Use [engineering conventions](engineering.md) for the lasting rules on
boundaries, modeling, pure decisions, ports, effects, readable conditions, and
type precision. [Testing](testing.md) owns test policy and observation
boundaries; [test ownership](test-ownership.md) owns cleanup decisions.
