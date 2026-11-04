# A-only exploratory run: execution record

## Human-readable summary

Across three high-effort runs, the reviewer caught 9, 10, and 11 of the 12
seeded violations, and correctly passed all 12 compliant controls in every
run. All missed violations were R4 resource-handling or error-translation
violations; the indexed R1 validation and R3 pure-decision violations were all
caught. The first run caught 75%, so high effort did not meet the requirement
to catch at least 80% in every repetition. The results cover only 24 private
controls per run, not the full corpus.

| Run | Violations caught | Violations missed |
| --- | ---: | ---: |
| 1 | 9 of 12 | 3 |
| 2 | 10 of 12 | 2 |
| 3 | 11 of 12 | 1 |

The [preflight](a-full-001-preflight.md) records the maintainer's explicit
override of the isolation gate before dispatch. The source input revision was
`15d44afad6f917cbc632a06688784a579e451535`; the clean invocation checkout was
`06730474d79ec443ec65ad54c488e9d3607a7775`, which added only that preflight.
No private labels or earlier model answers were supplied or inspected for this
run. Their separation from the model remains unverified. The override does not
establish isolation or complete the Evaluation.

All 12 scheduled A sessions ran once, sequentially, in predeclared order from
2026-11-04 08:45:14 UTC through 09:12:14 UTC, including gaps. No retries or
quota probes ran. Every direct child was reaped, with the final SIGKILL finding
no target, and every process exited zero. Captured events showed the known
disabled code-mode-host notice and no tool calls. Absence of tool events does
not prove tools were unavailable or reads isolated. The harness records the
requested model, effort and controls; server-side model, effort and effective
isolation remain unverified.

The public saved-result validator found eight structurally complete responses,
three invalid responses, and one incomplete response. The first none and low
responses included unknown public pairs; the final none response duplicated a
pair; the final low response omitted public pairs. Those observations remain in
the fixed schedule; none was replaced. Structural completeness says nothing
about correctness. Offline private scoring is reported below; no overall quality
conclusion follows.

| Repetition | Effort | Public state | Input | Output | Reasoning subset | Seconds |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1 | none | invalid | 30,831 | 7,206 | 0 | 140.895 |
| 1 | low | invalid | 15,400 | 6,164 | 0 | 113.914 |
| 1 | medium | complete | 15,398 | 5,638 | 372 | 108.247 |
| 1 | high | complete | 15,400 | 7,134 | 1,356 | 131.933 |
| 2 | low | complete | 15,400 | 5,810 | 231 | 108.809 |
| 2 | medium | complete | 15,402 | 6,202 | 455 | 116.892 |
| 2 | high | complete | 15,400 | 7,357 | 1,599 | 136.206 |
| 2 | none | complete | 15,404 | 5,776 | 0 | 107.821 |
| 3 | medium | complete | 15,398 | 5,713 | 305 | 108.938 |
| 3 | high | complete | 15,398 | 7,472 | 1,707 | 139.302 |
| 3 | none | invalid | 15,396 | 5,789 | 0 | 107.727 |
| 3 | low | incomplete | 15,400 | 3,246 | 181 | 62.658 |

Raw usage totals 200,227 input and 73,507 output tokens; 20,608 input tokens
were reported cached and 6,206 output tokens were reported as reasoning, a
subset of output. Sum of supervisor elapsed times is 1,383.342 seconds.
The first none observation's 30,831 input tokens greatly exceeded the dry-run
proxy, illustrating its limits. Subtracting the unreviewed candidate neutral
counts once per attempt gives 157,393 candidate adjusted input and 230,900
candidate adjusted complete tokens. These are estimates, not an established
baseline, hard consumption cap, cost or quality measure. Actual model usage
and automatic context remain subject to the provider's reporting limits.

[Original run trees, public validator reports, a series summary and SHA-256 manifest](../../../../../output/reviewer-evaluation/a-full-001/)
are retained. Original paths point to `/private/tmp/ataraxia-a-full-001-stage`;
byte-identical copies are stored in the linked directory without rewriting the
recorded paths. Saved-result reads of all 12 relocated runs reproduced the
original public state counts; this checks reader compatibility, not
authenticated lineage. The digest manifest covers all retained files except
itself.

Before any harness invocation, an initial `make eval` failed while uv tried to
fetch dependency metadata and DNS was unavailable. No run tree or model call was
created by that failure. `make verify-setup` confirmed the locked environment,
and the twelve actual invocations used `make eval UV_NO_SYNC=true` with the
preflight arguments. This changes dependency synchronization, not model-visible
inputs or the requested CLI profile. Public reports were generated from the
saved runs without reading the private reference. No B or C calls ran.

## Offline private scoring

The existing scorer matched the frozen reference SHA-256
`ddc084c2f2c168bef1dead140e508953688e3d721b7de56ee4e5aa53644febd8`
and bound the same source and rule digests across all twelve saved plans.
The [reference-only freeze](corpus/reference-freeze.md) records independent
agent review and acceptance before this run; it is not a human review or a
complete protocol freeze. The scorer conservatively labels the reference draft
and unreviewed and does not itself verify that freeze. Detailed scoring reports
remain outside the repository.

Each call has 24 fixed controls: 12 violation and 12 PASS. Entries below are
counts, not percentages. Accuracy is correct labels out of 24; recall is
correct violations out of 12; PASS is correct PASS labels out of 12; FP is
violations reported for PASS controls out of 12. Invalid and incomplete calls
have zero primary credit, including zero observed FP; that zero is not evidence
of clean passes. Complete-valid-only measures match the primary values for the
eight complete calls and are undefined for the four other calls (zero valid
denominators and 24 excluded opportunities each).

| Slot | State | Correct / 24 | Recall / 12 | PASS / 12 | FP / 12 | Public / 186 | Indexed / 24 | Determinate / 24 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rep1-none | invalid | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rep1-low | invalid | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rep1-medium | complete | 20 | 8 | 12 | 0 | 186 | 24 | 24 |
| rep1-high | complete | 21 | 9 | 12 | 0 | 186 | 24 | 24 |
| rep2-low | complete | 18 | 6 | 12 | 0 | 186 | 24 | 24 |
| rep2-medium | complete | 21 | 9 | 12 | 0 | 186 | 24 | 24 |
| rep2-high | complete | 22 | 10 | 12 | 0 | 186 | 24 | 24 |
| rep2-none | complete | 20 | 8 | 12 | 0 | 186 | 24 | 24 |
| rep3-medium | complete | 20 | 8 | 12 | 0 | 186 | 24 | 24 |
| rep3-high | complete | 23 | 11 | 12 | 0 | 186 | 24 | 24 |
| rep3-none | invalid | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| rep3-low | incomplete | 0 | 0 | 0 | 0 | 108 | 16 | 16 |

Per-rule counts below use four violation and four PASS controls for each rule.
Each cell is correct labels / 8, correct violations / 4, correct PASS / 4,
and false positives / 4, in that order. The same zero-credit and valid-only
limits apply to each rule.

| Slot | R1 | R3 | R4 |
| --- | --- | --- | --- |
| rep1-none | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| rep1-low | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| rep1-medium | 7 / 3 / 4 / 0 | 8 / 4 / 4 / 0 | 5 / 1 / 4 / 0 |
| rep1-high | 8 / 4 / 4 / 0 | 8 / 4 / 4 / 0 | 5 / 1 / 4 / 0 |
| rep2-low | 5 / 1 / 4 / 0 | 8 / 4 / 4 / 0 | 5 / 1 / 4 / 0 |
| rep2-medium | 5 / 1 / 4 / 0 | 8 / 4 / 4 / 0 | 8 / 4 / 4 / 0 |
| rep2-high | 8 / 4 / 4 / 0 | 8 / 4 / 4 / 0 | 6 / 2 / 4 / 0 |
| rep2-none | 7 / 3 / 4 / 0 | 8 / 4 / 4 / 0 | 5 / 1 / 4 / 0 |
| rep3-medium | 5 / 1 / 4 / 0 | 8 / 4 / 4 / 0 | 7 / 3 / 4 / 0 |
| rep3-high | 8 / 4 / 4 / 0 | 8 / 4 / 4 / 0 | 7 / 3 / 4 / 0 |
| rep3-none | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| rep3-low | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

All indexed records in these results were determinate; UNKNOWN and
NOT_APPLICABLE counts were zero. The incomplete final low response had 108 of
186 public records and 16 of 24 indexed records; those partial records did not
earn primary credit. Invalid responses have zero usable indexed records.
Unindexed responses were not scored. Repetitions reuse the same authored
controls and do not add incident diversity.

No effort condition establishes the protocol quality screen: isolation remains
unverified under the explicit override, and none and low also have incomplete
coverage. Even with complete medium and high public responses, at least one
repetition in each falls below the 80% violation-recall threshold. These are
label-agreement observations, not evidence of sound reasoning, finding
precision, authenticated isolation, or a strategy winner. No B comparison,
B execution, or Evaluation acceptance criterion follows from these results.
