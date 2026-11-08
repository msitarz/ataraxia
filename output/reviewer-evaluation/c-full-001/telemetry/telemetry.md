# C process and transport telemetry

2,232 of 2,232 CLI processes finished successfully; configured concurrency: 25;
2,228 responses were schema-complete and 4 were invalid. The previously
documented 22 recorded boundary-affected calls remain separate from these
structural counts.

852/2,232 (38.17%) attempts emitted reconnect notices and 567/2,232 (25.40%)
emitted HTTPS fallback notices; 567 had both and 1,380 had neither. These
include 3,057 reconnect and 567 fallback notices, and 3,624 status-403
occurrences across 852 attempts. Structured 429, 503, and -32001 occurrences
are 0, 0, and 0; unknown error events are 0. The notices describe recovery
within one CLI process, not harness retries. Recorded CLI versions: codex-cli
0.166.0. The Codex 0.166 source behavior examined in the earlier investigation
hides the first WebSocket retry; emitted notices do not count physical
attempts.

The recorded blocks each have 186 calls and one attempt per call. This
establishes completion for this workload with recovery, not an optimal
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

| Group | Recovery/attempts | Fallback % | Elapsed p50 s | Elapsed p95 s | Known/missing |
| --- | ---: | ---: | ---: | ---: | ---: |
| rep1-high | 67/186 | 26.88% | 11.86 | 36.22 | 186/0 |
| rep1-low | 51/186 | 18.82% | 7.76 | 32.63 | 186/0 |
| rep1-medium | 78/186 | 28.49% | 14.04 | 34.00 | 186/0 |
| rep1-none | 79/186 | 27.42% | 11.95 | 34.73 | 186/0 |
| rep2-high | 93/186 | 26.88% | 17.50 | 37.09 | 186/0 |
| rep2-low | 61/186 | 19.35% | 10.08 | 35.34 | 186/0 |
| rep2-medium | 73/186 | 28.49% | 10.96 | 38.65 | 186/0 |
| rep2-none | 61/186 | 18.82% | 9.40 | 36.38 | 186/0 |
| rep3-high | 93/186 | 30.65% | 17.31 | 38.05 | 186/0 |
| rep3-low | 65/186 | 26.88% | 9.58 | 36.31 | 186/0 |
| rep3-medium | 68/186 | 28.49% | 9.83 | 36.17 | 186/0 |
| rep3-none | 63/186 | 23.66% | 9.05 | 34.14 | 186/0 |
| none | 203/558 | 23.30% | 10.61 | 35.56 | 558/0 |
| low | 177/558 | 21.68% | 9.05 | 35.30 | 558/0 |
| medium | 219/558 | 28.49% | 11.72 | 37.15 | 558/0 |
| high | 253/558 | 28.14% | 13.97 | 37.55 | 558/0 |
| Recovery overall | 852/852 | 66.55% | 32.13 | 38.05 | 852/0 |
| No recovery overall | 0/1380 | 0.00% | 8.01 | 14.00 | 1380/0 |

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

HTTP status counts cover `unexpected status` diagnostics in error events, not
arbitrary answer text. Numeric -32001 counts cover direct and nested structured
error code fields only. Counts describe occurrences and distinct attempts; the
same 403 can appear in reconnect and fallback notices. Unknown error shapes are
counted separately. Original archives, inventories and launcher metadata are
verified before analysis; inspection checks internal consistency and byte
provenance, not authenticated lineage or safe-read enforcement. The pilot ran
first; the remaining blocks followed the recorded order. The next measurement
would vary concurrency on matched workloads and capture server-side timing if
available.
