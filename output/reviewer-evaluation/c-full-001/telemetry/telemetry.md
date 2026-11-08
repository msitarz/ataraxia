# C process and transport telemetry

All 2,232 CLI processes finished successfully at configured concurrency 25;
2,228 responses were schema-complete and 4 were invalid. The 22 previously
recorded boundary-affected calls remain separate from these structural counts.

852 attempts emitted reconnect notices and 567 emitted HTTPS fallback notices;
567 had both and 1,380 had neither. These include 3,057 reconnect and 567
fallback notices, and 3,624 status-403 occurrences across 852 attempts.
Structured 429, 503, and -32001 occurrences are 0, 0, and 0; unknown error
events are 0. The notices describe recovery within one CLI process, not harness
retries. The first WebSocket retry is hidden, so emitted notices do not count
physical attempts.

Each block has 186 calls and one attempt per call; all were run at concurrency
25. This establishes completion for this workload with recovery, not an optimal
concurrency, a subscription limit, or a speedup over serial execution. The 403
WebSocket diagnostics and fallback do not establish rate limiting. Server queue
time, inference time, and retry delays have no timestamps here. Process
activity is not inference.

| Block | Window seconds | Answers/min | Schema-complete/min | Peak active | Mean active | Start span seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| rep1-high | 136.75 | 81.61 | 81.61 | 25 | 23.39 | 119.46 |
| rep1-low | 143.31 | 77.87 | 77.87 | 25 | 16.66 | 84.54 |
| rep1-medium | 138.28 | 80.71 | 80.71 | 25 | 23.15 | 115.06 |
| rep1-none | 177.11 | 63.01 | 63.01 | 25 | 18.40 | 117.07 |
| rep2-high | 153.49 | 72.71 | 72.71 | 25 | 23.76 | 135.35 |
| rep2-low | 120.94 | 92.28 | 91.78 | 25 | 24.39 | 115.25 |
| rep2-medium | 142.48 | 78.33 | 78.33 | 25 | 22.73 | 119.25 |
| rep2-none | 122.44 | 91.15 | 90.66 | 25 | 24.23 | 114.16 |
| rep3-high | 161.58 | 69.07 | 69.07 | 25 | 23.55 | 141.07 |
| rep3-low | 120.67 | 92.48 | 92.48 | 25 | 24.50 | 115.13 |
| rep3-medium | 132.14 | 84.46 | 83.55 | 25 | 22.82 | 117.12 |
| rep3-none | 119.96 | 93.03 | 93.03 | 25 | 24.17 | 113.31 |

Windows span earliest process start through latest end; rates use each block's
window and exclude launch and cleanup outside it. Mean active is the integral
of simultaneous process intervals divided by that window. Intervals are half-
open; ties end before starts. Across all blocks, the union of active intervals
is 1669.14 seconds, while the actual first-start to last-end span is 4152.37
seconds, including idle gaps.

The JSON retains per-block, effort and all-attempt counts, token categories,
and elapsed distributions. Percentiles interpolate linearly at (n-1)p; each
distribution records known and missing counts. Elapsed seconds are supervisor
observations including startup and recovery. Recovery and no-recovery groups
differ in effort, timing, task and cache mix; their distributions do not
establish a causal latency effect. Cached input is included in input, and
reasoning is included in output. No cost is inferred.

Status counts cover structured `unexpected status` diagnostics in error events,
not arbitrary answer text. Counts describe emitted occurrences and distinct
attempts; the same 403 can appear in reconnect and fallback notices. Unknown
error shapes are counted separately. Original archives, inventories and
launcher metadata are verified before analysis; inspection checks internal
consistency and byte provenance, not authenticated lineage or safe-read
enforcement. The pilot ran first; the remaining blocks followed the recorded
order. The next measurement would vary concurrency on matched workloads and
capture server-side timing if available.
