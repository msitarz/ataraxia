# Make suite timing observations

## Declared protocol

Baseline is frozen at `96ef5bae2a322c3d1c5a530b88687e128742332c`, before test
cleanup, in the prepared worktree `/private/tmp/ataraxia-make-baseline`.
Worktree creation copied prepared caches, synchronized the locked environment
offline, and verified it. Host and installed package versions are retained in
`measurements/tools.json`; repository lockfile and Python minor version are
unchanged. Final measurements must match these conditions or explicitly report
deviations and limit comparison.

Every child-test invocation uses `UV_OFFLINE=true`, `UV_NO_SYNC=true`,
`GIT_CONFIG_GLOBAL=/dev/null`, and `GIT_CONFIG_NOSYSTEM=1`. Git isolation is a
protocol adjustment: previous verification failed at fixture commits under
inherited global SSH signing. Apply it to final measurements too; it affects
child tests only, not commits on this delivery branch.

Full selection is `make test ARGS=test/make/integration` with
`PYTEST_ADDOPTS='--durations=0'`. Unmarked selection uses the same command with
`PYTEST_ADDOPTS='--durations=0 -m "not real_tool"'`. Run one untimed warm-up
for each selection, followed by full/unmarked alternation three times. Run
sequentially on this host without another suite running concurrently.

Outer elapsed seconds use Python's monotonic performance clock immediately
before launching Make and immediately after its exit; startup, collection,
tests, reporting, and process exit are included. Preparation, warm-ups, and
artifact writing are excluded from measured medians. Pytest-reported test
elapsed time and per-test durations remain separate observations. Raw combined
stdout/stderr, commands, UTC start/end, exit status, and elapsed seconds are
retained under `measurements/`, including warm-ups (timed for diagnostics only).

Stop and report any timeout, failure, interruption, or unexpected skip; preserve
its output rather than silently retry. Three successful matched observations
per selection are required. Contract preservation is mandatory; timing cannot
justify removed coverage. No percentage speedup is assumed and no timing
assertions or new benchmark tool are introduced.

## Results

All eight invocations exited 0; no failures, errors, timeouts, interruptions, or
skips occurred. Three measured observations per selection completed in the
planned order. Warm-ups are retained but excluded from medians.

| Invocation / raw output | Outer elapsed (s) | Pytest elapsed (s) | Outcome |
| --- | --- | --- | --- |
| [warmup-full](measurements/warmup-full.txt) | 56.575 | 50.91 | 71 passed |
| [warmup-unmarked](measurements/warmup-unmarked.txt) | 36.581 | 35.64 | 50 passed; 21 deselected |
| [1-full](measurements/1-full.txt) | 48.804 | 47.78 | 71 passed |
| [1-unmarked](measurements/1-unmarked.txt) | 35.359 | 34.37 | 50 passed; 21 deselected |
| [2-full](measurements/2-full.txt) | 50.141 | 49.14 | 71 passed |
| [2-unmarked](measurements/2-unmarked.txt) | 37.284 | 36.22 | 50 passed; 21 deselected |
| [3-full](measurements/3-full.txt) | 48.728 | 47.78 | 71 passed |
| [3-unmarked](measurements/3-unmarked.txt) | 35.453 | 34.50 | 50 passed; 21 deselected |

Measured outer medians: full **48.804 s**;
unmarked **35.453 s**. Separate pytest elapsed
medians: full 47.78 s; unmarked 34.50 s. Per-test setup/call/teardown
durations are in the raw outputs; corresponding JSON files retain invocation
metadata. [Tool metadata](measurements/tools.json) records the frozen tools.

Across the six measured runs, the two slowest cases already use fake uv:
CI preparation (4.38–4.65 s call) and read-only documentation routing parity
(2.26–2.50 s call). See the duration sections in the six raw outputs above.
The baseline shows cost remains in orchestration subprocesses as well as
real-tool cases; it does not identify a causal overhead or establish a cleanup
speedup.

No protocol deviations occurred beyond the declared Git-isolation adjustment.
All measured invocations reused the prepared environment. This single-host,
three-repetition warm-cache baseline does not characterize cold starts, CI,
or general hardware performance. The two selections cover different workloads;
their timings are not a cleanup speedup comparison.

Final cleanup condition is pending; parent AC-2 remains TODO. Final measurements
must reproduce the declared environment/isolation and preserve required
contracts before a baseline/final timing conclusion can be assessed.
