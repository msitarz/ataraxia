# Draft review inputs

The source corpus comes from revision
`75f8f278753984604805341e1e94acb668d58c4e`. These static inputs prepare the
initial comparison in the
[protocol](../protocol.md). They are drafts for owner review, not a freeze or
permission to run trials.

- [Response schema](response.schema.json) defines the JSON envelope and fields.
- [Expected assessments](expected.json) lists the 24 public keys, without
  labels.
- [A prompt](a.txt) covers all keys, rules, and source files.
- B prompts cover one rule each: [R1](r1.txt), [R3](r3.txt), and [R4](r4.txt).
  Each contains the same complete source bundle as A.
- [C prompts](c/) cover one key each. [Range map](c-ranges.json) records their
  original source lines. Slices retain decorators, module contracts, imports,
  referenced local types and helpers, and enclosing class context where needed.
- [Prompt template](prompt-template.txt) records the common task wording.

Each prompt is complete except for its literal `{SESSION_ID}` placeholder.
For a future reviewed call list, replace exactly that placeholder with an opaque
session identifier unique to the fresh planned call. Preserve the remaining
bytes. Input IDs identify these prepared variants; trusted runtime records must
also distinguish all effective inputs, settings, and repetitions. Effort is
bound in those trusted records, not included in the model-visible prompt. This
preparation does not define the call list or perform runtime binding.

A complete response contains exactly one assessment for every expected key, with
no duplicate or foreign keys. Its identifiers must match the issued call. The
schema requires explanations for all judgments. A VIOLATION also requires a
source line span, exact quotation, consequence, and proposed severity. The line
span refers to the original file. Corrections are separate and may be empty. For
incomplete output, set `complete` to false and retain any partial assessments;
it cannot count as complete coverage. A later scorer must enforce exact sets,
issued identifiers, ordered line spans, source evidence, and completeness in
addition to the schema. The schema alone cannot establish these properties.

To check the prepared bytes against the public corpus, run from the repository
root:

```sh
make test ARGS=test/script/integration/eval/test_prepared_reviewer_inputs.py
```

The tests reconstruct all prompts from the template, schema, public rules and
source ranges, resolve the 24 targets with Python's AST, and check the public
sets. They do not establish semantic sufficiency, label correctness, or runtime
isolation. Independent owner review must assess those properties and the private
reference index before freeze. No private answers are needed for this check.
