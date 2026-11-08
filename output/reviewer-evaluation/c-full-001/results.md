# Static C results

Across 288 indexed opportunities, C caught 124 of 144 frozen violations and
correctly classified 136 of 144 PASS controls. Nineteen eligible violations were
missed; one violation was excluded for invalid output. Seven eligible PASS
controls were false positives and one PASS control was excluded for a denied
tool attempt. These are classifications against a small authored reference, not
independently adjudicated findings or evidence of historical generality.

At high effort, the three repetitions caught 12/12, 11/12, and 12/12
violations, with 1, 0, and 1 false positives respectively and no exclusions.
At medium effort they caught 10/12, 10/12, and 9/12; the third had one
invalid violation excluded. Each repetition has 12 violation controls and 12
PASS controls.

The fixed denominator is 12 violations and 12 PASS controls per block. Eligible
denominators remove invalid and boundary-affected calls; UNKNOWN and
NOT_APPLICABLE are neither PASS nor detected violations. The full 2,232-call
public inventory has 2,228 structurally complete outputs and four invalid JSON
outputs. All 22 boundary-affected calls are among the complete outputs, leaving
2,206 structurally complete, boundary-eligible calls. Twenty-one of those 22 do
not correspond to indexed controls.

## High and medium repetitions

| Block | Violations caught | Eligible missed | Violations excluded | Correct PASS | False positives | PASS excluded | UNKNOWN | NOT_APPLICABLE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rep1-medium | 10 | 2 | 0 | 11 | 1 | 0 | 0 | 0 |
| rep1-high | 12 | 0 | 0 | 11 | 1 | 0 | 0 | 0 |
| rep2-medium | 10 | 2 | 0 | 11 | 1 | 0 | 0 | 0 |
| rep2-high | 11 | 1 | 0 | 12 | 0 | 0 | 0 | 0 |
| rep3-medium | 9 | 2 | 1 | 12 | 0 | 0 | 0 | 0 |
| rep3-high | 12 | 0 | 0 | 11 | 1 | 0 | 0 | 0 |

## All effort totals

| Block | Violations caught | Eligible missed | Violations excluded | Correct PASS | False positives | PASS excluded | UNKNOWN | NOT_APPLICABLE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| none | 30 | 6 | 0 | 34 | 2 | 0 | 0 | 0 |
| low | 30 | 6 | 0 | 34 | 1 | 1 | 0 | 0 |
| medium | 29 | 6 | 1 | 34 | 2 | 0 | 0 | 0 |
| high | 35 | 1 | 0 | 34 | 2 | 0 | 0 | 0 |

Each effort total has fixed denominators of 36 violations and 36 PASS controls.
Eligible denominators equal those totals minus the respective exclusions.
Fixed-denominator recall is caught/36 and fixed correct-PASS rate is correct
PASS/36; valid-only rates divide by the eligible denominators. The per-rule
table below has four violations and four PASS controls per block.

## Per-rule and repetition counts

| Block | Violations caught | Eligible missed | Violations excluded | Correct PASS | False positives | PASS excluded | UNKNOWN | NOT_APPLICABLE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rep1-medium R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-medium R3 | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |
| rep1-medium R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-none R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-none R3 | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |
| rep1-none R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-low R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-low R3 | 4 | 0 | 0 | 2 | 1 | 1 | 0 | 0 |
| rep1-low R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-high R1 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep1-high R3 | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |
| rep1-high R4 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-low R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-low R3 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-low R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-medium R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-medium R3 | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |
| rep2-medium R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-high R1 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-high R3 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-high R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-none R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep2-none R3 | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |
| rep2-none R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-medium R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-medium R3 | 3 | 0 | 1 | 4 | 0 | 0 | 0 | 0 |
| rep3-medium R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-high R1 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-high R3 | 4 | 0 | 0 | 3 | 1 | 0 | 0 | 0 |
| rep3-high R4 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-none R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-none R3 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-none R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-low R1 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-low R3 | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| rep3-low R4 | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 0 |

## Resources and timing

Times are seconds from earliest attempt start to latest attempt end per block,
and the sum of supervisor-observed attempt durations, respectively. This attempt
window is not a measured launch-through-cleanup strategy wall time. At
concurrency 25, durations overlap; startup, reconnect, and fallback latency
remain included. UTC attempt timestamps and the original records are retained in
the archives.

| Block | Attempt window | Sum of attempt time | Input | Cached input | Output | Reasoning output | Candidate-adjusted input | Candidate-adjusted complete |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rep1-medium | 138.28 | 3200.66 | 965328 | 365440 | 7105 | 496 | 301308 | 308413 |
| rep1-none | 177.11 | 3258.5 | 975481 | 410496 | 6657 | 0 | 311461 | 318118 |
| rep1-low | 143.31 | 2387.25 | 997753 | 407424 | 6787 | 0 | 334105 | 340892 |
| rep1-high | 136.75 | 3198.32 | 959892 | 389760 | 31580 | 24594 | 295872 | 327452 |
| rep2-low | 120.94 | 2950.19 | 970426 | 480896 | 6626 | 0 | 306778 | 313404 |
| rep2-medium | 142.48 | 3238.36 | 960264 | 419328 | 6911 | 318 | 296244 | 303155 |
| rep2-high | 153.49 | 3646.81 | 959892 | 481152 | 33252 | 26275 | 295872 | 329124 |
| rep2-none | 122.44 | 2967.13 | 974193 | 480256 | 6629 | 0 | 310173 | 316802 |
| rep3-medium | 132.14 | 3014.82 | 965460 | 475776 | 7448 | 815 | 301440 | 308888 |
| rep3-high | 161.58 | 3805.44 | 959520 | 483840 | 34310 | 27323 | 295500 | 329810 |
| rep3-none | 119.96 | 2898.85 | 985660 | 509184 | 6759 | 0 | 321640 | 328399 |
| rep3-low | 120.67 | 2956.05 | 959892 | 483840 | 6574 | 0 | 296244 | 302818 |

Provider usage totals are 11,633,761 input tokens, including 5,387,392 cached
input; cache-write input is zero. Output is 160,638, including 79,821 reasoning
tokens. Categories are not additive where included. Candidate-adjusted input
subtracts per attempt the previously observed candidate baseline: 3,570 for
none, medium, and high; 3,568 for low. Negative adjustments are retained. These
baselines are estimates of overhead rather than enforced bounds.
Candidate-adjusted complete tokens add the full output to adjusted input. The
table retains raw categories; no cost is inferred.

## Execution and limits

The pilot ran first and is reused once as repetition 1 medium. The remaining
order was rep1 none, low, high; rep2 low, medium, high, none; rep3 medium, high,
none, low. All blocks used concurrency 25, not the protocol's serial setting or
the pilot's originally planned 3. Each contains 186 calls and one attempt per
call; there were no harness retries, probes or refills. Codex internally
performed transport reconnects and HTTPS fallback on some attempts; these are
included in the observed attempt records and latency. The pilot used head
`3e88202d`; other blocks used `6d06876d`. The intervening change was a code fix,
and the reviewed C source and prompt content is identical. Execution was
separately authorized with the known unverified isolation limitation.

The 22 flagged attempts each issued one code-mode `exec` call, and each
corresponding native session returned the disabled-host denial, with no
successful tool response. The boundary decision and positions were recorded
before private grading in [analysis-policy.json](analysis-policy.json);
[boundary-audit.json](boundary-audit.json) records the inspected session
identifiers and digests. All receive zero primary credit; retained outputs are
not erased. This observation does not establish tool-free execution or verified
isolation.

The public C manifest binds all 186 keys and exact shared, rule, function and
composed-prompt bytes to the frozen private index's source and rule hashes. The
private reference was reviewed by agents and frozen separately, not by a human
owner; its digest is in the policy. Independent rule-specific C context review
and a full C freeze were not completed. The authored fixtures do not establish
historical incident diversity. Acceptance criteria remain TODO; no production
policy or strategy selection follows from these results.

## Reproduction and retained evidence

The twelve compressed archives preserve each original block once.
[inventory.json](inventory.json) indexes per-block inventories mapping every
original and relative path to byte count and SHA-256, and records archive
checksums. Launcher and pre-execution records
are retained alongside them. No native session contents are included. Verify and
restore to a new directory, then run offline scoring with the separately held
frozen index and a new private output file:

```sh
make reviewer-c-verify-archive CLI_ARGS='--evidence output/reviewer-evaluation/c-full-001 --destination /absolute/new/extracted-directory'
make reviewer-c-score CLI_ARGS='--manifest doc/feat/reviewer/engineering/evaluation/inputs/c-manifest.json --policy output/reviewer-evaluation/c-full-001/analysis-policy.json --identities output/reviewer-evaluation/c-full-001/block-identities.json --reference /absolute/private/index.md --runs /absolute/new/extracted-directory --output /absolute/new/private-score.json'
```

The verifier checks archive and member hashes, inventory, duplicates and path
safety, and inspects the restored runs without rewriting the recorded paths.
Inspection checks internal consistency, not authenticated lineage or safe-read
enforcement. [aggregate.json](aggregate.json) contains the C-only aggregate
values underlying these tables; keyed classifications remain private.

The identity and ordered packet mapping in
[block-identities.json](block-identities.json) was recorded after grading during
review. It binds the original pre-grading policy by its unchanged SHA-256; it is
factual provenance, not a new pre-grading policy. The score command writes a
private keyed score file and a companion `-aggregate.json` containing
reproducible public counts and resources.

For offline process and transport analysis, see the
[telemetry report](telemetry/telemetry.md),
[machine summary](telemetry/telemetry.json), and
[per-attempt metrics](telemetry/telemetry-attempts.csv). Reproduce the
retained artifacts without provider access:

```sh
make reviewer-c-telemetry CLI_ARGS='--evidence output/reviewer-evaluation/c-full-001 --output output/reviewer-evaluation/c-full-001/telemetry --check'
```

The check compares the observations and reports any changes in the analysis
code digests separately. The retained machine summary keeps the original
generation's code provenance.
