# Code fixture draft

**Status:** frozen draft, pending independent review. Historical source/test
blobs, overlay, and replay checks are verified; no trial has run and no
dispatch is authorized.

## Executor-facing draft

**Task:** implement bounded `BarProvider` CSV validation in the prepared
checkout. Malformed row shape, invalid numeric values, and invalid CSV syntax
must raise `ProviderError` with the shard path and original parse exception
preserved as `__cause__`. Invalid or missing headers must also identify the
shard. Preserve valid rows and ordering, blank-row skipping, normal exhaustion,
context-manager requirements, and provider cleanup on success and failure.
Add focused tests for malformed input and those preserved behaviors. Change
only `src/ataraxia/provider.py` and `test/unit/test_provider.py`. Return the
patch and check results. Do not commit, push, or create a PR.

**Prompt to finalize:**

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

**Expected outcome:** malformed rows and CSV syntax raise contextual
`ProviderError` with `ValueError` or `csv.Error` as the cause; invalid and
missing headers identify the shard; valid records, blanks, exhaustion, and
context-manager behavior remain correct; handles close on success and failure;
focused tests cover these cases and pass.

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
- **Preservation inventory:** the baseline has tests for valid single-bar
  reads, `StopIteration`, bad/missing headers, use outside a context manager,
  and path-based hashability. The reference adds malformed field-count/value
  tests with path context, chained `ValueError`, and cleanup; blank-row
  skipping; empty-header exhaustion and cleanup; and unterminated-quote
  `csv.Error` chaining and cleanup. Preserve these observed behaviors; no
  historical patch is included in the executor context.
- **Environment and replay proof:** a probe worktree was prepared from f7.
  An unpinned setup selected Python 3.14.6; setting `UV_PYTHON=3.14.7` before
  `make ci-setup UV_OFFLINE=true` recreated the environment on CPython 3.14.7.
  `make verify-setup` then passed. On the exact f4 overlay, the focused provider
  suite passed (6 tests), `make lint-check` and `make format-check` passed, and
  `make typecheck` exited 0 (strict check clean; expected negative cases
  reported). Pin `UV_PYTHON=3.14.7` for all 18 worktrees and stop if that
  interpreter or the f7 lock/tool setup is unavailable.
- **Evidence links:** the direct commit permalinks above are parent-only
  references. The executor sees only the task prompt and prepared tree and is
  explicitly instructed not to inspect history, refs, tags, or parent-only
  material.

This is a frozen draft for independent review. It does not authorize dispatch;
the controlled comparison remains blocked on protocol approval and explicit
maintainer authorization.
