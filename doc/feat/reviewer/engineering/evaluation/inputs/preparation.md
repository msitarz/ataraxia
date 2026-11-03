# Draft review inputs

The source corpus comes from revision
`75f8f278753984604805341e1e94acb668d58c4e`. These static inputs prepare the
initial A/B comparison in the [protocol](../protocol.md). They are drafts for
owner review, not a freeze or permission to run trials.

- [Shared instructions and response schema](shared/review-instructions-and-schema.txt)
  is the single common file supplied to every call.
- The [A case](cases/A/a.txt) contains all three rules.
- B cases contain one rule each: [R1](cases/B/r1.txt), [R3](cases/B/r3.txt), and
  [R4](cases/B/r4.txt). All calls use the same
  [whole corpus](corpus/source.txt).
- Private controls and rationales are held separately and are not supplied to
  the model. C preparation is deferred.

Supply the shared directory first, followed by one case directory and the common
corpus directory. The generic harness's default `\n\n` separator places the
shared file before each case and the corpus after it:

```sh
# A: one case
-d doc/feat/reviewer/engineering/evaluation/inputs/shared \
-d doc/feat/reviewer/engineering/evaluation/inputs/cases/A \
-d doc/feat/reviewer/engineering/evaluation/inputs/corpus

# B: three independent cases
-d doc/feat/reviewer/engineering/evaluation/inputs/shared \
-d doc/feat/reviewer/engineering/evaluation/inputs/cases/B \
-d doc/feat/reviewer/engineering/evaluation/inputs/corpus
```

The response has a boolean `complete` and a findings list. A completed review
may have no findings. Each finding identifies the rule and original file, line
span and quotation, explanation, consequence, and severity; optional corrections
are separate. The
[response validator](../../../../../../script/reviewer_eval/validation.py)
checks the schema, supplied-rule and file membership, ordered in-bounds line
spans, and exact UTF-8 quote bytes within the original span. LF separates source
lines; CRLF and other original bytes are preserved for matching. It retains
duplicate findings for owner adjudication and incomplete findings for inspection
without quality credit.

This pure core does not extract CLI JSONL, verify process status, provenance,
settings or immutable reads, judge findings, match private answers, score, or
deduplicate. Callers and owner adjudication must provide those guarantees. It
is an initial increment, not a trial-readiness gate. Trusted call records bind
runtime identity and settings outside model-visible material.

Check the prepared bytes from the repository root:

```sh
make test ARGS=test/script/integration/eval/test_prepared_reviewer_inputs.py
```

The tests compare each case with the rule bytes and the shared bundle with the
source bytes, inspect the shared schema and envelope, and compose the actual
directories through the pure plan builder. Independent owner review of the
inputs and private reference index, runtime binding, baselines, boundary
verification, call list, and a new freeze remain outstanding. No private answers
are needed for this check.
