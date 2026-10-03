# Leaf-agent comparison results

**Decision:** retain Luna-low as the default. The documentation fixture did not
meet either predeclared improvement threshold. Sol-low qualifies numerically as
a candidate for a broader same-task-class coding comparison, but reference
contamination makes comparative effectiveness uncertain. Recommend only that
comparison after input isolation and prompt/rubric alignment, retaining the
current default. These results support no deployment or default inference. Any
further comparison needs its own reviewed protocol and explicit authorization;
no further dispatch is authorized here.

## Aggregate results

All 18 final artifacts passed the owning parent’s correctness, preservation,
scope, and required-check gates. Eight initial artifacts required one
consolidated correction round; there were no replacements and no human steering.
Findings are initial-review counts. Time is dispatch through final parent
review, including waits.

| Fixture | Condition | Initial accepts | Final pass | Correction rounds | Median end-to-end (range), s | Initial findings B/M/m | Parent review windows total, s |
| --- | --- | ---: | ---: | ---: | --- | --- | ---: |
| Documentation | Luna-low | 2/3 | 3/3 | 1 | 90 (72–217) | 1/0/0 | 68 |
| Documentation | Luna-medium | 2/3 | 3/3 | 1 | 87 (87–129) | 0/1/0 | 68 |
| Documentation | Sol-low | 3/3 | 3/3 | 0 | 77 (74–83) | 0/0/0 | 41 |
| Code | Luna-low | 0/3 | 3/3 | 3 | 375 (348–424) | 5/4/0 | 217 |
| Code | Luna-medium | 0/3 | 3/3 | 3 | 336 (317–380) | 5/5/0 | 178 |
| Code | Sol-low | 3/3 | 3/3 | 0 | 201 (176–266) | 0/0/1 | 105 |

A candidate qualifies only if all nine final gates pass and either it has at
least two more initial accepts out of three than Luna-low with median time no
more than 25% higher, or its median time is at least 20% lower with no worse
initial acceptance or correction-round count. The figures below are compared
per fixture under this rule.

B/M/m = blocking/material/minor. The numerical Sol-low result is uncertain as a
comparative-effect estimate because reference solution material was available
through the modern Git index/base view for all nine code runs. Direct
observations or reports of visibility occurred in C1, C2, A2, A3, and B3,
spanning all three conditions. The worktree overlay and setup did not change
mid-trial. This realizes the protocol’s residual-leakage risk; it does not
establish that any particular artifact copied the reference. It supports no
deployment or default inference.

## Per-run record

Order is documentation A1/B1/C1, B2/C2/A2, C3/A3/B3, then the same sequence for
code. Initial is unchanged acceptance under the frozen rubric. Findings are
blocking/material/minor. `D` means reported documentation format, link, and diff
checks passed and were reused; they were rerun after corrections. `R` means
reported required code checks passed after any correction; `O` is the parent
oracle result. These are reported outcomes, not archived complete stdout.

| Run | Condition | Initial | Rounds | End-to-end, s | Review window, s | Findings B/M/m | Check evidence |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| doc-A1 | Luna-low | No | 1 | 161–217* | 42 | 1/0/0; broadened delegation scope | D pass |
| doc-B1 | Luna-medium | Yes | 0 | 87 | 11 | 0/0/0 | D pass |
| doc-C1 | Sol-low | Yes | 0 | 83 | 16 | 0/0/0 | D pass |
| doc-B2 | Luna-medium | Yes | 0 | 87 | 15 | 0/0/0 | D pass |
| doc-C2 | Sol-low | Yes | 0 | 74 | 14 | 0/0/0 | D pass |
| doc-A2 | Luna-low | Yes | 0 | 72 | 14 | 0/0/0 | D pass |
| doc-C3 | Sol-low | Yes | 0 | 77 | 11 | 0/0/0 | D pass |
| doc-A3 | Luna-low | Yes | 0 | 90 | 12 | 0/0/0 | D pass |
| doc-B3 | Luna-medium | No | 1 | 129 | 42 | 0/1/0; duplicate effort wording remained | D pass |
| code-A1 | Luna-low | No | 1 | 375 | 79 | 1/1/0; shape error translation and missing Raises docs | R pass; O 10/12→12/12 |
| code-B1 | Luna-medium | No | 1 | 336 | 79 | 1/2/0; broad TypeError handling, missing docs, vacuous cleanup assertions | R pass; O 12/12 |
| code-C1‡ | Sol-low | Yes | 0 | 176 | 49 | 0/0/0 | R pass; O 12/12 |
| code-B2 | Luna-medium | No | 1 | 317 | 54 | 2/2/0; overflow, broad catches, missing docs, cleanup assertions | R pass; O 11/12→12/12 |
| code-C2‡ | Sol-low | Yes | 0 | 201 | 47 | 0/0/1; iterator error documented at class level | R pass; O 12/12 |
| code-A2‡ | Luna-low | No | 1 | 424 | 68 | 1/1/0; blank-record suppression, cleanup assertions | R pass; O 12/12 |
| code-C3 | Sol-low | Yes | 0 | 266 | 9 | 0/0/0 | R pass; O 12/12 |
| code-A3‡ | Luna-low | No | 1 | 348 | 70 | 3/2/0; overflow, broad catches/skips, docs and cleanup | R pass; parent reran typecheck (exit 0) |
| code-B3‡ | Luna-medium | No | 1 | 380 | 45 | 2/1/0; overflow, broad catch, missing docs | R pass; O 11/12→12/12 |

`*` doc-A1 has adjacent dispatch observations at 08:49:20 and 08:50:16 UTC; they
bound the interval but do not measure a 56-second dispatch call. This gives an
end-to-end bound of 161–217 seconds; the median is unchanged. The reported
documentation range uses the conservative 217-second upper bound. `‡` Modern
reference solution material was observed or reported visible in the
working-tree/index view for that run. B1 had a transient lint failure that was
corrected and passed; C1 had a transient lint failure then passed; C2 had a
transient docstring lint adjustment; A3’s typecheck was reported nonzero but the
parent rerun exited 0. C3 code review began after context recovery; the wait is
included in its unadjusted end-to-end time. No adjusted speed figures are
substituted.

The coding prompt asked to preserve the original parse exception, while the
review rubric expected `ValueError` specifically for malformed row shape. This
prompt/rubric specificity mismatch creates ambiguity in interpreting shape-cause
findings; no causal attribution is measured. Align them before any new coding
comparison. The same root GPT-6 reviewer knew
conditions and prior results throughout; reasoning effort is unknown. The sample
is three runs per condition and task, ordered and sequential, so host/tool noise
and context effects remain material.

## Measurements and checks

The authorization followed integration of protocol revision
`efdc21a1316fd381d29ab5002bd818233e7fbb43` in master
`617fe22c2637122c7eba90d84241b2faba1794ca`. Every run used runtime base
`f7e03b6237ac240b41e784d1e9cdd4dac1118ccd`, CPython 3.14.7, uv 0.12.19, and
lockfile blob `833f068eb5e02edcc6863c22b10c1f4ecb3c4107`. Documentation used
`doc/orchestrator.md` blob `cd886039148f5c3af1d8adf6aeed42c2443a1909`; code used
only provider/test blobs `a58ff8db591248553ecc6c91abe2932aceea80d6` and
`3b93bc902f94145464e52353010519e3176a6a67` as the worktree overlay. The
record reports no setup change mid-trial.

Executor active time, active parent-review time, exact human review time, token
and cost data, some finding-delivery timestamps, and some leaf start timestamps
are unavailable and remain unknown. Review windows above must not be treated as
active effort. Preparation took 190 seconds from recorded initial start to just
before the first dispatch; per-run setup overhead is unknown and outside the
end-to-end intervals. Protocol preparation was reported separately (PR #121) and
was not timed. This results-reporting session was outside the 18-dispatch cap
and did no trial work. The doc-A1 dispatch interval and code-C3 context-recovery
wait are included without adjustment.

Required-check outcomes were reported by the leaf and reused in parent review;
documentation checks were not repeated except after corrections. Focused parent
code probes were additional evidence. The initial code oracle returned 10/12
for A1 (shape-cause expectations) and 11/12 for B2 and B3 (overflow); final
oracles returned 12/12. A2’s 12/12 oracle was supplemented by source review that
found overbroad blank-record suppression. A3’s original parent oracle produced
1/12 because it assumed `provider.fd` remained set after exit; the executor
cleared that field. A revised probe retained the actual file handle and passed
12/12 with the same input, cause, and value assertions. No acceptance gate
changed. The extra A3 probe, check, and report work are included in its review
window, which is still not active-time evidence.

Complete raw check stdout was not captured. The recorded checks, timestamps,
review findings, prompts, frozen-input identities, and patch snapshots are in
[`evidence.tar.gz`](evidence.tar.gz). It contains exactly 29 files: the raw JSON
record, 18 initial patches, eight corrected final patches, and the two parent
oracle probes. The probes are historical evidence only; they are not installed
or retained as production tests. No repository tests were added for this Work.
The two archived parent-oracle probes are inspection-only evidence, not
repository tests. Archive SHA-256:
`a3b1753cfa8c6a5100e6203d018f6e5a153f9dffae0398d6140f3cbf966fe8da`. Extract its
flat contents with
`tar -xzf evidence.tar.gz -C /private/tmp/leaf-trial-evidence` (after creating
that destination directory). The current Luna-low default remains in force
pending a separately reviewed and authorized comparison.
