# A-only exploratory run: execution record

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
pair; the final low response omitted public pairs. Those observations remain
in the fixed schedule; none was replaced. Structural completeness says nothing
about correctness. Private scoring and quality conclusions remain outstanding.

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
