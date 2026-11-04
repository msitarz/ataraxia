# B-only exploratory run: public accounting

All 36 scheduled slots settled: 16 publicly complete, 19 invalid, and one
failed. There were no incomplete or not-started slots and no timeouts. Public
completion validates response shape and correspondence to the frozen input;
it does not establish semantic correctness or the execution boundary. No
private scoring below measures agreement with a draft, independently unreviewed
reference; it does not establish correctness or boundary readiness. No A/B
comparison has been performed.

## Classification agreement

Each condition combines three separately scored calls. Its fixed denominator is
24 controls: 12 expected violations and 12 expected passes. Publicly complete
responses supplied 16 of 36 calls; 15 remain eligible for primary credit after
the manual boundary gate described below. A failed, invalid, or boundary-gated
call earns zero fixed-denominator credit and excludes four violation and four
pass opportunities from the valid-only view. An excluded violation is
unobserved, not a demonstrated semantic miss.

| Rep | Effort | Public complete | Eligible | Violations caught / 12 | Uncaught among eligible | Excluded violations | Correct passes / 12 | False positives | Excluded passes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | none | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 12 |
| 1 | low | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 12 |
| 1 | medium | 2 | 2 | 7 | 1 | 4 | 8 | 0 | 4 |
| 1 | high | 2 | 2 | 8 | 0 | 4 | 8 | 0 | 4 |
| 2 | low | 1 | 0 | 0 | 0 | 12 | 0 | 0 | 12 |
| 2 | medium | 3 | 3 | 11 | 1 | 0 | 12 | 0 | 0 |
| 2 | high | 2 | 2 | 8 | 0 | 4 | 8 | 0 | 4 |
| 2 | none | 1 | 1 | 4 | 0 | 8 | 4 | 0 | 8 |
| 3 | medium | 1 | 1 | 3 | 1 | 8 | 4 | 0 | 8 |
| 3 | high | 2 | 2 | 7 | 1 | 4 | 8 | 0 | 4 |
| 3 | none | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 12 |
| 3 | low | 2 | 2 | 7 | 1 | 4 | 8 | 0 | 4 |

Every eligible pass control was classified PASS or VIOLATION; the table's
false-positive counts are violations assigned to expected PASS controls.
Among eligible calls, uncaught violations include any non-VIOLATION response;
they are not necessarily explicit PASS judgments. Across conditions, fixed
credit is 55 of 144 violation controls and 60 of 144 pass controls. The
valid-only view is 55 of 60 violations and 60 of 60 passes, with zero false
positives among those 60 passes; 84 violation and 84 pass opportunities are
excluded. These are control agreement counts, not a findings precision claim.

| Repetition | Public complete / 12 | Eligible / 12 | Violations caught / 48 | Correct passes / 48 | False positives |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 4 | 4 | 15 | 16 | 0 |
| 2 | 7 | 6 | 23 | 24 | 0 |
| 3 | 5 | 5 | 17 | 20 | 0 |

| Rule | Public complete / 12 | Eligible / 12 | Violations caught / 48 | Correct passes / 48 | False positives |
| --- | ---: | ---: | ---: | ---: | ---: |
| R1 | 2 | 2 | 7 | 8 | 0 |
| R3 | 8 | 7 | 28 | 28 | 0 |
| R4 | 6 | 6 | 20 | 24 | 0 |

The boundary-gated repetition 2 / low / R3 call's raw agreement is diagnostic
only: four of four violations caught and four of four passes correct, with no
false positives. It contributes no primary quality credit while its eight
controls remain in the fixed denominator. Its condition cannot pass the
boundary screen. No label adjudication or overall quality-screen conclusion is
established by these counts.

The
[preflight](../../../doc/feat/reviewer/engineering/evaluation/b-full-001-preflight.md)
records the initial authorization, exact inputs and limits. The caller and
inputs were at `7a20635c98bda0adb47dda43c91459929b2e2041`. The
[slot inventory](slots.json) records every call's public outcome, diagnostic,
time and available raw usage. The table aggregates the three scheduled rules per
condition; it does not compare one rule's cost to a full strategy.

| Rep | Effort | Complete | Invalid | Failed | Raw input | Raw output | Candidate adjusted input | Seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | none | 0 | 2 | 1 | 27,910* | 7,686* | 20,770* | 145.5 |
| 1 | low | 0 | 3 | 0 | 41,212 | 9,379 | 30,508 | 181.6 |
| 1 | medium | 2 | 1 | 0 | 41,212 | 10,235 | 30,502 | 196.4 |
| 1 | high | 2 | 1 | 0 | 41,212 | 12,167 | 30,502 | 231.4 |
| 2 | low | 1 | 2 | 0 | 55,196 | 13,061 | 44,492 | 247.0 |
| 2 | medium | 3 | 0 | 0 | 41,208 | 7,011 | 30,498 | 137.9 |
| 2 | high | 2 | 1 | 0 | 41,210 | 11,878 | 30,500 | 225.6 |
| 2 | none | 1 | 2 | 0 | 41,212 | 13,691 | 30,502 | 257.5 |
| 3 | medium | 1 | 2 | 0 | 41,218 | 14,008 | 30,508 | 263.7 |
| 3 | high | 2 | 1 | 0 | 41,220 | 12,247 | 30,510 | 230.6 |
| 3 | none | 0 | 3 | 0 | 41,212 | 10,076 | 30,502 | 194.8 |
| 3 | low | 2 | 1 | 0 | 41,210 | 7,108 | 30,506 | 141.9 |

\* The failed first call supplied no usage, so the repetition 1 / none values
are the known subtotal for two calls, not the three-call total. All other rows
sum three calls, including invalid responses. Seconds sum supervisor-observed
attempt elapsed times and exclude preparation, review and paused time.

Raw input/output subtotals by repetition are 151,546/39,467 for repetition 1
(11 of 12 calls with usage), 178,826/45,641 for repetition 2, and
164,860/43,439 for repetition 3. Known input and output across 35 calls are
495,232 and 128,547 respectively; the full 36-call total is unknown. Cached
input across those 35 calls is 19,072. Reasoning output is 3,984, 4,576, and
4,308 by repetition and is a subset of output, not an additional total.
Usage fields retain their provider meanings; cost is unavailable.

Candidate adjusted input subtracts 3,570, 3,568, 3,570, or 3,570 per observed
attempt for none, low, medium, or high respectively. These prior neutral
observations include the neutral prompt and are not reviewed frozen baselines;
the subtraction is an uncertain candidate estimate. It is not a hard token
limit or a cost measure. The full bounds and hard-enforcement limitation are
in the preflight.

## Boundary deviations and execution

The first call, repetition 1 / none / R1, failed during CLI startup in the
restricted outer host sandbox. Its stderr records a failed open of the disabled
memories database and app-server initialization denied by the host. No response
or usage was recorded. The failed open does not establish a successful read.
The failed slot was retained and not retried.

An initial request for expanded host permission was rejected by automatic
approval review because the specific payload and destination were not explicit.
The user then authorized the prepared shared instructions, selected B rule,
authored freight-code corpus and minimal instructions to OpenAI through the
installed Codex `gpt-6-luna` for the remaining 35 attempts, excluding private
index and prior answers. [authorization.txt](authorization.txt) preserves the
instruction. Subsequent calls used expanded outer host permission, while the
requested model controls and inputs remained unchanged.

Repetition 2 / low / R3 requested a code-mode tool inventory; the host denied it
before execution. Dispatch stopped. The owner inspected only that call's native
session and found one inventory-filter request and its matching
`code-mode host is disabled` denial, with no other tool calls or observed file
content. The native session path is
`/Users/nzs/.codex/sessions/2026/11/04/rollout-2026-11-04T12-51-05-01a1a666-00a5-79b3-a5a8-0700c52efac9.jsonl`,
SHA-256 `d9f16a872ca9dc8d17691097812405dc07d05a4eb5c6220b4a306778c4e62eb2`. The
public validator classified this response complete; that classification is
retained separately from this boundary deviation and is not a tool-free or
quality-screen claim. After the user's instruction to continue, the owner
reviewed the denial and authorized the original remaining slots without refills.
[resumption.txt](resumption.txt) records the narrowed continuation. Other
completed processes emitted the accepted pre-turn disabled-code-host notice.
Effective isolation and server-side model and effort binding remain unverified.

## Evidence

Original run directories remain under
`/private/tmp/ataraxia-b-full-001-staging`; the retained directories here are
byte-identical copies, with absolute stream references pointing to those
original paths. Every public report was generated against its original run.
[SHA256SUMS](SHA256SUMS) records all 252 copied run and report files, verified
against the originals. Each slot has one attempt and there were no quota probes
or replacements.

The private index SHA-256 is
`ddc084c2f2c168bef1dead140e508953688e3d721b7de56ee4e5aa53644febd8`.
The 36 detailed reports and aggregate helper are retained outside the checkout
in `/Users/nzs/ataraxia-eval-results/reviewer-b-full-001-scores`. Their private
manifest SHA-256 is
`e45b7125622feef696dec4a0a7b2f9df64fafee0d0e217da75b336180307bbb4`.
For each `RUN` in [slots.json](slots.json), reproduce the private score into a
new exclusive `PRIVATE_OUTPUT` using:

```sh
uv run --cache-dir .cache/uv --no-sync python -m script.reviewer_eval /private/tmp/ataraxia-b-full-001-staging/RUN --reference-index /Users/nzs/ataraxia-eval-results/reviewer-initial-corpus-private/index.md --output PRIVATE_OUTPUT
```

Each single-case score exits 1 because its own strategy group lacks the other
two rules; its per-call measures remain available. The retained `aggregate.py`
reads the explicit slot inventory and private per-call scores, verifies the
eight-control denominators and reference digest, and sums the three calls per
condition. It excludes the flagged call's credit without modifying its raw
score. Run it from the checkout root with `python3
/Users/nzs/ataraxia-eval-results/reviewer-b-full-001-scores/aggregate.py`.
Its output includes only aggregate counts and the separately flagged diagnostic.

The result is incomplete for the Evaluation's quality and boundary criteria;
independent review and private adjudication remain.
