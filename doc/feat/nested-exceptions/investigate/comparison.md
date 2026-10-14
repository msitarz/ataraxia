# Pinned Ruff comparison

Ruff 0.16.8 is pinned in `uv.lock`. `pyproject.toml` enables preview and
SIM, but selects neither TRY nor PLR1702. `make lint-check ARGS=...` runs
Ruff on the selected paths and then an advisory PLR0915 pass.

## Observations

The exact matrix sources and candidate configurations are preserved as text in
[`test/make/fixtures/nested-exceptions-probe`](../../../../test/make/fixtures/nested-exceptions-probe/).
Each candidate `ruff.toml` extends the repository configuration. Ruff's
official documentation supports this
[`extend` arrangement](https://docs.astral.sh/ruff/configuration/); the pinned
binary accepted it. The `.txt` suffix keeps candidate configurations and
intentionally diagnostic input out of normal lint hooks. To reproduce a run,
temporarily rename the source to `.py` and the selected config snapshot to
`ruff.toml`, execute its Make command below from the worktree root, then restore
the original names.

The exact historical seed function is preserved at
[`seed/seed.py.txt`](../../../../test/make/fixtures/nested-exceptions-probe/seed/seed.py.txt).
It is extracted from original line 349 of
[`script/sandbox.py` at `47779e4`](https://github.com/msitarz/ataraxia/blob/47779e4dbf3df31d0c4ebcffd9d074ba493ccff3/script/sandbox.py#L349-L392).
The seed probe used the same candidate settings as the matrix probes, via the
two `seed/*.ruff.toml.txt` snapshots. No sandbox operation was executed.

| Candidate and setting | Observed matrix result | Assessment |
| --- | --- | --- |
| PLR1702, `max-nested-blocks = 1` | Matrix: 10 diagnostics, including all five nested-handler arrangements. Seed: 2 diagnostics at the outer `try`. | Too broad. Five matrix diagnostics are false positives for allowed branch/loop structure, handler/cleanup nesting in either direction, a context manager and a nested function's handler. The count does not establish the handler-specific rule or execution-scope boundary. |
| TRY300 and TRY301 | No diagnostics for the matrix or historical seed. | Misses the proposed violation. TRY300 checks for `return` statements in a `try` block; TRY301 addresses explicit raises caught by that same `try`. |

Exact commands from the worktree root:

```sh
make lint-check ARGS=test/make/fixtures/nested-exceptions-probe/plr1702/matrix.py
make lint-check ARGS=test/make/fixtures/nested-exceptions-probe/try/matrix.py
# First with seed/plr1702.ruff.toml.txt exposed as seed/ruff.toml:
make lint-check ARGS=test/make/fixtures/nested-exceptions-probe/seed/seed.py
# Then with seed/try.ruff.toml.txt exposed as seed/ruff.toml:
make lint-check ARGS=test/make/fixtures/nested-exceptions-probe/seed/seed.py
```

The PLR1702 matrix run emitted ten diagnostics (Make exited 2 after Ruff
exited 1): line 2 `handler_body`, line 12 `handler_in_handler`, line 22
`handler_in_else`, line 34 `handler_in_finally`, line 57 `branches_and_loops`,
line 66 `cleanup_only`, line 76 `cleanup_parent`, line 86 `context_manager`,
line 94 `nested_function` and line 106 `async_handlers`. Lines 2, 12, 22, 34
and 106 are the five required rejections; lines 57, 66, 76, 86 and 94 are
allowed arrangements rejected by the broad block count. Sequential synchronous
handlers (line 46) and sequential async `except*` handlers (line 115) emitted
no diagnostic.

On the historical seed, PLR1702 emitted two diagnostics at extracted line 13,
both on the outer `try` (original source line 361): nested-block counts 2 and
3, each greater than one. Make exited 2 after Ruff exited 1. TRY300 and TRY301
reported `All checks passed!` on both the seed and the whole matrix, with Make
exiting 0. The separate advisory PLR0915 pass reports 29 statements for the
seed function, above its advice threshold of 25, but exits successfully.

Official rule descriptions:
[PLR1702](https://docs.astral.sh/ruff/rules/too-many-nested-blocks/)
counts nested blocks and defaults to five;
[TRY300](https://docs.astral.sh/ruff/rules/try-consider-else/) checks for
`return` statements in `try` blocks;
[TRY301](https://docs.astral.sh/ruff/rules/raise-within-try/) addresses explicit
raises caught by the same `try`. These descriptions align with the observed
gaps; current online docs are not used as evidence for pinned-version behavior.

## Seed and repair inventory

The historical seed at `47779e4` has nested handler-bearing tries in
`_open_stable_lock`: the exclusive-create race handler is inside the
`FileNotFoundError` handler, and validation/descriptor cleanup uses a nested
`try`/`finally`. The observed PLR1702 diagnostics flag the outer `try` twice but
do not distinguish these handlers from ordinary nesting; TRY300/TRY301 produce
no diagnostics. The seed code is no longer present at this Work's assigned
base `5c431a8` (`script/sandbox.py` no longer defines `_open_stable_lock`).

Manual inventory covered the repository's Python lint scope: `src/`, `script/`,
`test/` and `example/`. No nested handler-bearing `try` within one execution
scope was found at the assigned base. Every production handler is in a function
without a nested handler-bearing `try`; the handlers in
`test/script/unit/test_work_paths.py` and `test/ataraxia/unit/test_source.py`
are each in separate test functions. `example/` has no `try` handlers. The
present repair inventory is therefore empty. Recheck the integrated source
before adoption, since this inventory is specific to base `5c431a8`.

## Recommendation and gap

Ruff 0.16.8's inspected candidates do not enforce the exact contract. PLR1702
is not a suitable substitute, and TRY300/TRY301 miss the rule. The exact rule
needs handler-aware lexical scope tracking, including `except*` and excluding
nested functions. This investigation recommends no current Ruff setting as
precise enforcement.

Adoption therefore needs maintainer choice: wait for Ruff to provide a
supported precise rule, or explicitly authorize investigation and review of a
minimal alternative. This finding does not authorize a custom checker or
complete the parent's paired guidance-and-enforcement outcome.
