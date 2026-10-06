# Matched Make timing observations

This report refreshes the pre-cleanup baseline; final comparison is pending.
The [original report](measurements.md) and its raw artifacts remain unchanged.
Use the [parent protocol](README.md#timing-protocol).

## Frozen conditions and preparation

Baseline code: `96ef5bae2a322c3d1c5a530b88687e128742332c`, prepared in
`/private/tmp/ataraxia-measurement-baseline-input`. Final code is frozen at
`72b5c0617e41fe01520f03095aaaea5317dc94c0` in
`/private/tmp/ataraxia-measurement-final-input`; its measured invocations have
not started. Both detached checkouts are evaluation inputs, not delivery bases.
Keep them, their environments and caches for the final Evaluation.

Read-only path/symlink and runtime inventory found existing Python 3.14.6 at
`/usr/local/bin/python3.14` and 3.14.7 through the local-bin alias. Standard
uv-managed interpreter directories were absent; this does not claim a complete
system-wide inventory. Choose 3.14.6 for both inputs, matching the original
baseline patch and freshly prepared delivery environment. This choice is for
measurement only. The initial uv inventory failed on its default user cache;
its escalated retry was aborted. Recovery found zero measured invocations;
filesystem/runtime inventory resolved preparation before this eight-run batch.
See [preparation notes](matched-measurements/baseline/preparation-notes.txt).

Both caches were copied from the same prepared main cache before setup. Their
initial normalized path/content fingerprints match: 9,888 files and 658,764,289
bytes each; see
[cache metadata](matched-measurements/baseline/initial-cache.json). Both inputs
passed offline `make ci-setup` then `make verify-setup` with scoped
`UV_PYTHON=/usr/local/bin/python3.14` and their own `UV_CACHE_DIR`. Retained
[baseline setup](matched-measurements/baseline/prepare-baseline.txt),
[final setup](matched-measurements/baseline/prepare-final.txt),
[baseline verification](matched-measurements/baseline/verify-baseline.txt) and
[final verification](matched-measurements/baseline/verify-final.txt) show no
remaining environment changes. Installed packages, lockfile fingerprint,
interpreter match. The identical selection command/filter was frozen before
execution; discovery/marker configuration equality was recorded afterward from
the frozen files, rather than included in the initial metadata check.

[Preflight metadata](matched-measurements/baseline/preflight.json) freezes host
`michals-mbp-2.home`, macOS 26.6.2, Python 3.14.6, uv 0.12.19, GNU Make 3.81,
Git 2.55.0 and package versions. A retained
[post-baseline check](matched-measurements/baseline/post-baseline.json) confirms
unchanged interpreter, tool/package versions, lock and environment metadata. Do
not alter these conditions before final execution; recheck matching first.

## Execution and results

Exactly eight baseline invocations ran sequentially: full/unmarked warm-ups,
then three alternating full/unmarked pairs, each with a 180-second timeout.
Commands were `make test ARGS=test/make/integration`, with `UV_OFFLINE=true`,
`UV_NO_SYNC=true`, `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, the
frozen interpreter/environment/cache, and `PYTEST_ADDOPTS='--durations=0'`.
Unmarked selection adds `-m "not real_tool"`. No concurrent suite ran.

Outer time uses `time.perf_counter()` immediately around Make launch/wait.
Preparation, warm-ups and post-exit artifact writing are excluded from medians;
pytest elapsed/durations are separate. Raw combined output is captured during
execution; each sibling JSON retains command, relevant environment, UTC
boundaries, exit, elapsed seconds and summary. The retained one-off
[timing command](matched-measurements/baseline/timer-command.txt) shows budget,
clock and stop handling; it adds no project target or benchmark framework.

| Invocation / raw output | Outer elapsed (s) | Pytest elapsed (s) | Outcome |
| --- | --- | --- | --- |
| [warmup-full](matched-measurements/baseline/warmup-full.txt) | 56.074 | 50.37 | 71 passed |
| [warmup-unmarked](matched-measurements/baseline/warmup-unmarked.txt) | 35.506 | 34.54 | 50 passed; 21 deselected |
| [1-full](matched-measurements/baseline/1-full.txt) | 50.640 | 49.53 | 71 passed |
| [1-unmarked](matched-measurements/baseline/1-unmarked.txt) | 36.195 | 35.08 | 50 passed; 21 deselected |
| [2-full](matched-measurements/baseline/2-full.txt) | 50.667 | 49.66 | 71 passed |
| [2-unmarked](matched-measurements/baseline/2-unmarked.txt) | 37.243 | 36.18 | 50 passed; 21 deselected |
| [3-full](matched-measurements/baseline/3-full.txt) | 49.883 | 48.83 | 71 passed |
| [3-unmarked](matched-measurements/baseline/3-unmarked.txt) | 36.910 | 35.81 | 50 passed; 21 deselected |

Measured outer medians: full **50.640 s**; unmarked **36.910 s**. Separate
pytest elapsed medians: full 49.53 s; unmarked 35.81 s. See
[summary metadata](matched-measurements/baseline/summary.json) for unrounded
outer medians. Warm-ups are excluded. All eight invocations exited 0, without
failures, errors, skips, timeouts or interruptions; the eight-run budget is
exhausted with no extra invocations. Preparation interruption is disclosed
above; there was no measured-sequence deviation. Recording the immutable pytest
configuration comparison after the batch is a preflight-order deviation; it does
not establish that final tests have been executed.

This is a single-host, three-repetition warm-cache baseline. It does not measure
cold starts, CI or general hardware performance. Full and unmarked selections
are different workloads; their medians are not a cleanup speedup comparison.
Final measurements, preservation review and parent acceptance remain pending.
No causal or general speedup claim follows from baseline refresh alone.
