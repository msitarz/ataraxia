# Draft review inputs

The source corpus comes from revision
`75f8f278753984604805341e1e94acb668d58c4e`. These static inputs prepare the
initial A/B comparison in the [protocol](../protocol.md). The shared prompt and
validator implement `function-assessments-v2`. A new independent review and
freeze remain required. These artifacts are not permission to run trials.

- [Shared instructions and response schema](shared/review-instructions-and-schema.txt)
  is the single common file supplied to every call.
- The [A case](cases/A/a.txt) contains all three rules.
- B cases contain one rule each: [R1](cases/B/r1.txt), [R3](cases/B/r3.txt), and
  [R4](cases/B/r4.txt). All calls use the same
  [whole corpus](corpus/source.txt).
- Private controls and rationales are held separately and are not supplied to
  the model. Complete or account for all 12 A calls before any of the 36 B
  calls.
- C preparation and execution follow A/B comparison, review, and new
  authorization.

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

The [response validator](../../../../../../script/reviewer_eval/validation.py)
checks each assessment against the supplied rules and the public AST-derived
function inventory. Missing pairs are retained as incomplete; labels are model
classifications, not verified truth. Private grading is outside this increment.
[Saved reviewer results](../../../../../../script/reviewer_eval/README.md)
selects the response format from frozen shared prompt provenance and retains
legacy findings interpretation for historical runs.

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
