# Code fixture draft

**Status:** independently reviewed frozen fixture, pending integration and
explicit maintainer authorization. Historical source/test blobs, overlay, and
replay checks are verified; no trial has run and no dispatch is authorized.

## Executor handoff

**Exact executor prompt:**

> Work from the prepared checkout only. In `src/ataraxia/provider.py`, make
> malformed CSV row shapes, invalid numeric values, and invalid CSV syntax raise
> `ProviderError` with the shard path; preserve the original parse error as
> `__cause__`. Invalid and missing headers must identify the shard. Preserve
> valid row values and ordering, blank-row skipping, normal exhaustion,
> context-manager requirements, and provider cleanup on success and failure. Add
> focused regression tests in `test/unit/test_provider.py` for malformed rows
> and syntax, valid and blank input, exhaustion, exception causes, header
> context, and cleanup. Do not inspect Git history, refs, tags, historical
> patches, or parent-only fixture material. Change no other file. Run
> `make test ARGS=test/unit/test_provider.py`,
> `make lint-check ARGS='src/ataraxia/provider.py test/unit/test_provider.py'`,
> `make format-check ARGS='src/ataraxia/provider.py test/unit/test_provider.py'`,
> and `make typecheck`. Return the patch and results. Do not commit, push, or
> create a PR.

Use this exact prompt for all nine runs of this fixture. The parent prepares the
historical overlay before handoff; the leaf receives no reference commit or
parent-only material.

## Owning-parent rubric and preservation inventory

Keep these baseline behaviors distinct from the new requirements. The frozen
f4 source/tests establish valid single-bar parsing, numeric normalization and
values, row order, normal `StopIteration`, blank-row skipping by `DictReader`,
`ProviderError` when iterated outside a context manager, filepath-based
hashability, and file closure when the context manager exits. Preserve these
behaviors. The reference-focused replay probe below identifies which new
requirements fail on this baseline; it does not prove the implementation.

The following examples define the new acceptance criteria. `P` means the
fixture's concrete shard path. For each malformed row or CSV syntax case,
iteration must raise `ProviderError` whose message includes `P`; its `__cause__`
must be the underlying exception shown. The open file must be closed after the
provider context exits, including when iteration raises.

| Input after the canonical header | Required outcome |
| --- | --- |
| `1,100` | `ProviderError` includes P; `ValueError` cause (too few columns) |
| `1,100,200,50,150,1,extra` | `ProviderError` includes P; `ValueError` cause (too many columns) |
| `1,bad,200,50,150,1` | `ProviderError` includes P; `ValueError` cause (invalid integer) |
| `1,,200,50,150,1` | `ProviderError` includes P; `ValueError` cause (empty numeric value) |
| `1,1.0e999,200,50,150,1` | `ProviderError` includes P; `OverflowError` cause (non-finite normalization) |
| `1,"100,200,50,150,1` | `ProviderError` includes P; `csv.Error` cause (unterminated quote) |

An incorrect header such as `timing,open,high,low,close,volume`, a headerless
row `1,2,3,4,5,6`, and a zero-byte file must each raise `ProviderError` whose
message includes P; the file closes on context exit. No parse cause is
required for header rejection. A file
containing only `timestamp,open,high,low,close,volume` followed by newline is
valid and empty: iteration reaches normal exhaustion and the handle closes on
context exit. With canonical header plus blank lines around rows
`1,100,200,50,150,1` and `2,100,200,50,150,1`, yielded timestamps must be
`[1, 2]`, in that order, with no blank record; the handle closes on context
exit. A valid single row must retain the baseline parsed values and must then
exhaust normally.

**Checks:** `make test ARGS=test/unit/test_provider.py`,
`make lint-check ARGS='src/ataraxia/provider.py test/unit/test_provider.py'`,
`make format-check ARGS='src/ataraxia/provider.py test/unit/test_provider.py'`,
and `make typecheck`. These were run against the prepared baseline; rerun them
for every trial artifact.

## Owning-parent-only material — exclude from leaf handoffs

- **Runtime and guidance base:**
  [f7e03b6](https://github.com/msitarz/ataraxia/commit/f7e03b6237ac240b41e784d1e9cdd4dac1118ccd).
  Keep its `AGENTS.md`, guidance, `Makefile`, `.python-version`,
  `pyproject.toml`, and `uv.lock`; do not check out historical instructions or
  dependencies. `.python-version` is `3.14`; `pyproject.toml` pins uv `0.12.19`;
  the lockfile blob is `833f068eb5e02edcc6863c22b10c1f4ecb3c4107`.
- **Historical input:** the pre-change source and tests are from
  [f4eddb1](https://github.com/msitarz/ataraxia/commit/f4eddb18802fa8601989bce61ea5aec814384825),
  the parent of broad commit
  [3dd4bf6](https://github.com/msitarz/ataraxia/commit/3dd4bf6ee55cb4e094ba0227759faf0d13cbe89a).
  The immutable f4 blobs are `a58ff8db591248553ecc6c91abe2932aceea80d6`
  (`src/ataraxia/provider.py`) and
  `3b93bc902f94145464e52353010519e3176a6a67`
  (`test/unit/test_provider.py`). The reference blobs at 3dd are
  `d1f16b0589f43823c8d114d6d7a3e6877233cde0` and
  `39c26c657edccde67551844fd119a7bbda1fc643`. The verified f4→3dd reference
  diff touches only those files: 77 insertions and 4 deletions. The changed
  files at f7 match 3dd exactly.
- **Deterministic overlay:** in every fresh worktree based on the single
  recorded modern trial base, the parent runs
  `git restore --source=f4eddb18802fa8601989bce61ea5aec814384825 --worktree -- src/ataraxia/provider.py test/unit/test_provider.py`.
  Verify only those two paths differ from the modern base and that
  `git diff --exit-code f4eddb18802fa8601989bce61ea5aec814384825 -- src/ataraxia/provider.py test/unit/test_provider.py`
  succeeds. This overlay restores historical task inputs only; it does not copy
  the answer patch or historical tooling/guidance. Keep these identifiers and
  commands out of the leaf handoff.
- **Reference gap probe:** the immutable 3dd reference tests were temporarily
  supplied to the f4 baseline in the probe worktree, without changing source.
  `UV_PYTHON=3.14.7 make test ARGS=test/unit/test_provider.py` reported 8
  passed and 5 failed: missing and extra columns escaped as `TypeError`, bad
  and empty numeric fields escaped as `ValueError`, and an unterminated quote
  escaped as `ValueError` instead of `ProviderError`. The exact f4 test blob
  was restored immediately afterward and verified; no reference tests remain
  in the fixture. Header-only exhaustion, blank-row skipping, and cleanup
  reference tests passed. Keep the new error requirements above separate from
  the verified baseline-preservation list.
- **Exception scope:** match the historical reference behavior by wrapping
  `ValueError`, `OverflowError`, and `csv.Error` as `ProviderError` with the
  shard path and original exception as cause. The overflow example above
  exercises `round(float("1.0e999") * 4)`. Header validation raises
  `ProviderError` with the shard path; the reference does not chain a parse
  exception for header failures.
- **Environment and replay proof:** a probe worktree was prepared from f7.
  An unpinned setup selected Python 3.14.6; setting `UV_PYTHON=3.14.7` before
  `make ci-setup UV_OFFLINE=true` recreated the environment on CPython 3.14.7.
  `make verify-setup` then passed. On the exact f4 overlay, the focused provider
  suite passed (6 tests), `make lint-check` and `make format-check` passed, and
  `make typecheck` exited 0 (strict check clean; expected negative cases
  reported). Pin `UV_PYTHON=3.14.7` for all 18 worktrees and stop if that
  interpreter or the f7 lock/tool setup is unavailable.
- **Evidence boundary:** the executor sees the exact task prompt and prepared
  tree, and is instructed not to inspect history, refs, tags, or parent-only
  material. This instruction does not prevent repository-object or other-file
  access; reference leakage remains a documented confound.

This reviewed frozen fixture does not authorize dispatch. The controlled
comparison remains blocked on integration and explicit maintainer
authorization.
