# Offline A/B/C comparison

There is **no formal protocol winner**. On the primary medium-effort
comparison, every strategy falls below the required 80% violation recall in at
least one repetition, and the required boundary and review evidence is
incomplete. The protocol's improvement test also requires both compared
strategies to pass the complete quality screen. The observed differences do not
satisfy that test.

C at high effort is the strongest observed classification candidate on this
small authored control set. It caught 12, 11, and 12 of 12 violations, with
one, zero, and one false positives, respectively. It is a reasonable next
prototype candidate for the engineering owner to consider, subject to the
maintainer's decision and representative context and testing before production.
This secondary observation does not replace the primary comparison, select
production policy, establish statistical significance, or complete the
Evaluation.

## Reading the results

A uses one whole-corpus, three-rule call; B uses three whole-corpus,
one-rule calls; C uses 186 function/rule calls. Each condition covers the same
186 public function/rule pairs. Each repetition has 24 indexed controls: 12
expected violations and 12 expected PASS labels. Repetitions reuse the same
controls, not new incidents. Unindexed public outputs are structurally checked,
not semantically scored. Classification agreement is not proof of reasoning,
finding precision, or whole-corpus accuracy.

Each table cell below is **caught / correct PASS / false positives / excluded
violations / excluded PASS**. Fixed-denominator recall is caught/12,
correct-PASS rate is correct PASS/12, false-positive rate is false positives/12,
and operational accuracy is (caught + correct PASS)/24. Excluded controls get
no fixed-denominator credit; they are unobserved, not semantic misses or clean
passes. For the eligible-only view, subtract the respective exclusions from 12
before dividing. Eligible missed violations are 12 minus caught minus excluded;
all eligible PASS controls in these results were determinate. C's indexed
UNKNOWN and NOT_APPLICABLE counts are zero; A's complete indexed outputs are
determinate. B's eligible uncaught violations may include other labels.

### Primary: medium effort

| Repetition | A | B | C |
| --- | --- | --- | --- |
| 1 | 8 / 12 / 0 / 0 / 0 | 7 / 8 / 0 / 4 / 4 | 10 / 11 / 1 / 0 / 0 |
| 2 | 9 / 12 / 0 / 0 / 0 | 11 / 12 / 0 / 0 / 0 | 10 / 11 / 1 / 0 / 0 |
| 3 | 8 / 12 / 0 / 0 / 0 | 3 / 4 / 0 / 8 / 8 | 9 / 12 / 0 / 1 / 0 |

Operational accuracy by repetition is A 20/24, 21/24, 20/24; B 15/24,
23/24, 7/24; and C 21/24 in all three. The 80% recall threshold requires at
least 10 of 12 in **every** repetition. A fails all three; B fails repetitions
1 and 3; C fails repetition 3. C exceeds A's recall by 2, 1, and 1 controls
(16.7, 8.3, and 8.3 percentage points), so even apart from the screens it does
not meet the ten-point improvement guard in every repetition.

### Secondary: high effort

| Repetition | A | B | C |
| --- | --- | --- | --- |
| 1 | 9 / 12 / 0 / 0 / 0 | 8 / 8 / 0 / 4 / 4 | 12 / 11 / 1 / 0 / 0 |
| 2 | 10 / 12 / 0 / 0 / 0 | 8 / 8 / 0 / 4 / 4 | 11 / 12 / 0 / 0 / 0 |
| 3 | 11 / 12 / 0 / 0 / 0 | 7 / 8 / 0 / 4 / 4 | 12 / 11 / 1 / 0 / 0 |

Accuracy is A 21/24, 22/24, 23/24; B 16/24, 16/24, 15/24; and C 23/24
(95.8%) in each repetition. C's high numerical recall, correct-PASS, accuracy,
and false-positive rates meet their individual thresholds in all repetitions.
All 558 C/high public outputs were structurally complete and none had the
recorded boundary flag. That does not establish the full quality screen:
independent rule-specific C context review, a full freeze, and retained
protections remain incomplete or unverified. A/high fails recall in repetition
1; B/high fails recall in all three. C has false positives where A and B have
none on their eligible controls; B's smaller eligible denominator makes zero
observed false positives no proof of immunity.

### Other effort observations

These rows retain the other scheduled conditions without pooling efforts into a
winner. The cell definition and denominators above still apply.

| Effort and repetition | A | B | C |
| --- | --- | --- | --- |
| none 1 | 0 / 0 / 0 / 12 / 12 | 0 / 0 / 0 / 12 / 12 | 10 / 11 / 1 / 0 / 0 |
| none 2 | 8 / 12 / 0 / 0 / 0 | 4 / 4 / 0 / 8 / 8 | 10 / 11 / 1 / 0 / 0 |
| none 3 | 0 / 0 / 0 / 12 / 12 | 0 / 0 / 0 / 12 / 12 | 10 / 12 / 0 / 0 / 0 |
| low 1 | 0 / 0 / 0 / 12 / 12 | 0 / 0 / 0 / 12 / 12 | 10 / 10 / 1 / 0 / 1 |
| low 2 | 6 / 12 / 0 / 0 / 0 | 0 / 0 / 0 / 12 / 12 | 10 / 12 / 0 / 0 / 0 |
| low 3 | 0 / 0 / 0 / 12 / 12 | 7 / 8 / 0 / 4 / 4 | 10 / 12 / 0 / 0 / 0 |

## Public validity and boundaries

The following entries are public complete calls / planned calls; parentheses
show calls eligible after the recorded boundary gate. A and B invalid or
incomplete calls exclude all controls assigned to that call. For C, a flagged
or invalid call excludes its one indexed control if it corresponds to one.
A's partial final low output is not credited.

| Effort and repetition | A | B | C |
| --- | --- | --- | --- |
| none 1 | 0/1 (0) | 0/3 (0) | 186/186 (183) |
| none 2 | 1/1 (1) | 1/3 (1) | 185/186 (182) |
| none 3 | 0/1 (0) | 0/3 (0) | 186/186 (181) |
| low 1 | 0/1 (0) | 0/3 (0) | 186/186 (179) |
| low 2 | 1/1 (1) | 1/3 (0) | 185/186 (183) |
| low 3 | 0/1 (0) | 2/3 (2) | 186/186 (186) |
| medium 1 | 1/1 (1) | 2/3 (2) | 186/186 (185) |
| medium 2 | 1/1 (1) | 3/3 (3) | 186/186 (186) |
| medium 3 | 1/1 (1) | 1/3 (1) | 184/186 (183) |
| high 1 | 1/1 (1) | 2/3 (2) | 186/186 (186) |
| high 2 | 1/1 (1) | 2/3 (2) | 186/186 (186) |
| high 3 | 1/1 (1) | 2/3 (2) | 186/186 (186) |

B's low repetition 2 has one publicly complete call excluded after a denied
host-tool request. C has 2,228 complete outputs of 2,232 and 22 boundary
flags among complete outputs; 21 flagged calls are unindexed. Its medium
repetition 3 also has an invalid indexed violation. The flagged calls retain
zero credit. Public completeness alone does not verify execution isolation.
The original records contain the full boundary decisions and retained failures.

## Resources and comparability

Raw input / output tokens for complete strategy runs, including invalid calls,
are shown below for the primary and high-effort conditions. B combines all
three calls; C combines all 186.

| Effort and repetition | A input / output | B input / output | C input / output |
| --- | --- | --- | --- |
| medium 1 | 15,398 / 5,638 | 41,212 / 10,235 | 965,328 / 7,105 |
| medium 2 | 15,402 / 6,202 | 41,208 / 7,011 | 960,264 / 6,911 |
| medium 3 | 15,398 / 5,713 | 41,218 / 14,008 | 965,460 / 7,448 |
| high 1 | 15,400 / 7,134 | 41,212 / 12,167 | 959,892 / 31,580 |
| high 2 | 15,400 / 7,357 | 41,210 / 11,878 | 959,892 / 33,252 |
| high 3 | 15,398 / 7,472 | 41,220 / 12,247 | 959,520 / 34,310 |

Across all 12 conditions, A used 200,227 input and 73,507 output tokens. B's
35 calls with known usage used 495,232 input and 128,547 output tokens; its
failed startup call reported no usage, so its full 36-call total is unknown.
C's 2,232 calls used 11,633,761 input and 160,638 output tokens. These
whole-series totals describe the schedules, not an overall winner across
unlike efforts. They include invalid calls. Cached input is a subset of input;
reasoning output is a subset of output, so neither should be added again.
The source records provide per-condition raw, cached, reasoning, and candidate
adjusted values. The adjustment subtracts neutral observations that are not
reviewed matched frozen baselines; it is uncertain and does not establish
billing or cost.

C used concurrency 25; A and B used one. C's recorded attempt window is not
launch-through-cleanup strategy wall time, and overlapping attempts make it
incomparable to A/B serial elapsed time as a speedup. C's much larger call
count also adds orchestration and input overhead. No detection-per-token or
cost winner follows from these observations.

## Provenance and limits

This offline comparison uses the published aggregate counts in the
[A execution record](a-full-001-execution.md) and
[series summary](../../../../../output/reviewer-evaluation/a-full-001/series-summary.json),
[B accounting](../../../../../output/reviewer-evaluation/b-full-001/README.md),
and [C results](../../../../../output/reviewer-evaluation/c-full-001/results.md)
and
[aggregate](../../../../../output/reviewer-evaluation/c-full-001/aggregate.json),
under the [protocol](protocol.md). A/B public transport revalidation is
[retained separately](../../../../../output/reviewer-evaluation/ab-transport-revalidation-001/README.md).
Counts above are copied or calculated by addition and the fixed denominators; no
private index, private score regeneration, or unindexed scoring was used. The
comparison uses the records integrated at
`45ef6255a73366c86a2696d30c78441a0a4b9cd1`.

A and B used CLI version 0.166.0, but runs differed in order, source and prompt
packaging, and execution context; see their preflights and the C manifest for
exact hashes. C's pilot ran first and is reused once as medium repetition 1;
its head was `3e88202d`, and later blocks used `6d06876d`. The C record says
reviewed C source and prompt content was identical across those heads. The C
manifest binds source and rule hashes to the reference, but function-specific
contexts and composed prompts differ from whole-corpus A/B. These changes,
order, concurrency, and opaque automatic context and server-side model/effort
binding confound causal attribution. The reference was independently reviewed
by agents, not a human owner; the authored corpus lacks historical incident
diversity. Source preservation, withheld labels and prior-answer isolation are
not established by observed tool denials. The existing Evaluation criteria and
engineering decision remain open.
