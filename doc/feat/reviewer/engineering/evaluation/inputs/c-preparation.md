# Static C preparation

These public artifacts prepare the
[C extension](../protocol.md#static-c-preparation-extension). They authorize no
model, neutral, or quota calls. Independent owner review of all packets, an
approved freeze and reconciled execution and budget authorization remain
required. Evaluation acceptance criteria remain TODO.

The AST inventory selects all 62 functions and methods in the frozen three-file
corpus and crosses them with R1, R3 and R4, producing 186 packets. Every packet
contains one explicit target and exact rule bytes. Its context consists of
original source spans: module contract and imports, lexical declarations,
target, and statically referenced module declarations and transitive callees.
Other functions are context, not assessment targets. The same source context is
used for all three rules for a given function. For example, a packet targeting
`Ledger.add_event` contains its original class declarations and the `save_event`
helper; only `Ledger.add_event` is assessed.

The [manifest](c-manifest.json) records whole-source byte counts and SHA-256
hashes, rule and shared-prompt hashes, target identities, source spans, roles,
reasons and span hashes. Every packet flags independent rule-specific context
review: static names cannot prove sufficient context or resolve all dynamic
calls or caller contracts. No current packet is flagged as approaching a whole
module; this does not establish sufficiency or eligibility. The public
[schedule](c-schedule.json) retains every pair in rule/file/function order with
three rotated effort repetitions. Private controls do not enter generation.

The manifest gives exact rendered prompt byte counts and a per-packet rough
`utf8-bytes-divided-by-four-v1` token proxy, rounded up. This heuristic is not a
provider tokenizer and may be substantially inaccurate. A full 186-call
strategy at one effort and repetition contains 1,372,568 supplied prompt bytes,
roughly 343,211 proxy tokens; the 12 blocks total 16,470,816 bytes and 4,118,532
proxy tokens. Shared instructions and context are repeated in each packet total;
the separate instruction file, automatic CLI/system framing, output, retries,
actual usage and cost are excluded and remain unknown. Estimate quality cannot
support a token-budget guarantee.

The 2,232 prospective calls have 2,232 no-retry attempts. For planning only, the
A/B per-call maximum of three additional attempts would imply up to 8,928
attempts, subject to a new reviewed global ceiling; it is not authorization. At
300 seconds plus 10 seconds cleanup, no-retry serial capacity at the bound is
about 192.2 hours before delays or preparation, exceeding the existing 40-hour
trial deadline. The existing 48-call and 208-total-attempt bounds cannot fund C.
**Budget refusal:** do not dispatch the matrix under those bounds. A future
execution decision must reconcile its full calls, retries, tokens, elapsed time,
evidence, output, reference review and scoring budgets and stop policy. The
unverified effective binding for each effort remains a prerequisite.

Generate and verify locally, without calls:

```sh
make reviewer-c-prepare
make reviewer-c-prepare CLI_ARGS=--check
make test ARGS='test/script/integration/eval/test_prepared_reviewer_c.py test/script/integration/eval/test_prepared_reviewer_inputs.py test/script/unit/reviewer_eval test/script/integration/reviewer_eval'
```

The generic matrix can be previewed for one effort as follows. The dry run
makes no model call; its tokenizer may require a cached vocabulary. It does not
enforce a token or money budget. Do not remove `-n` without the prerequisites
above, a newly reviewed freeze, explicit execution authorization, reconciled
budgets, and a separately chosen evidence destination.

```sh
make eval CLI_ARGS='-d doc/feat/reviewer/engineering/evaluation/inputs/c-shared -d doc/feat/reviewer/engineering/evaluation/inputs/c-packets -i doc/feat/reviewer/engineering/evaluation/preparation/min.md -m gpt-6-luna -e medium -c 1 -n'
```

The dry-run matrix has 186 calls, not the entire rotated schedule; run the
other efforts only for offline previews. The retained schedule is prospective,
not a dispatch command. Historical A/B observations remain separate, with
order, time, provider-load and cache confounds. No scoring implementation or
private-reference review is included in this preparation.
