# Reviewer harness smoke trial

From a clean repository root after these inputs are merged, prepare the locked
environment with `make ci-setup` and `make verify-setup`. Install the system
Codex CLI on `PATH` and use an authenticated subscription session. Choose a
fresh persistent output path; this example creates only its parent:

```sh
mkdir -p "$HOME/ataraxia-eval-results"
```

Preview the complete matrix without starting Codex or creating output:

```sh
uv run --no-sync python -m script.eval \
  -d doc/feat/reviewer/engineering/evaluation/smoke-trial/rules \
  -d doc/feat/reviewer/engineering/evaluation/smoke-trial/sources \
  -i doc/feat/reviewer/engineering/evaluation/smoke-trial/instructions.md \
  -m gpt-6-luna -e none -e low -c 1 \
  --timeout-seconds 120 --cleanup-timeout-seconds 10 \
  --output-limit-bytes 65536 --retry-limit 0 --capacity-retry-limit 0 \
  -o "$HOME/ataraxia-eval-results/reviewer-smoke12-001" -n
```

Confirm the preview reports 12 calls. When ready, run the same settings without
`-n`. The output directory must not already exist; choose a new name if it does:

```sh
uv run --no-sync python -m script.eval \
  -d doc/feat/reviewer/engineering/evaluation/smoke-trial/rules \
  -d doc/feat/reviewer/engineering/evaluation/smoke-trial/sources \
  -i doc/feat/reviewer/engineering/evaluation/smoke-trial/instructions.md \
  -m gpt-6-luna -e none -e low -c 1 \
  --timeout-seconds 120 --cleanup-timeout-seconds 10 \
  --output-limit-bytes 65536 --retry-limit 0 --capacity-retry-limit 0 \
  -o "$HOME/ataraxia-eval-results/reviewer-smoke12-001"
```

Can the harness account for this small matrix and retain inspectable model
outputs? The matrix is two rule files × three synthetic source files × one
model × two efforts = 12 planned calls. The rule comes first and source second,
joined by the harness's default two LF characters. Each launched call has one
harness attempt. Quota waiting is off, so there are no extra quota probes; both
retry limits are zero. These 12 CLI calls exclude any internal Codex retries and
the harness's local Codex version query. The installed system Codex is not
pinned. The dry run uses the real tokenizer and may download vocabulary on
first use; it makes no model call.

Completion requires accounting for all 12 planned calls and complete artifacts
for inspection. Retain failures and interruptions; fewer launched calls make
this smoke incomplete. Do not automatically rerun or replace failed calls.
Inspect `plan.json`, `run.json`, `events.jsonl`, and per-attempt records under
`attempts/`. The raw Codex JSONL is in each attempt's `.stdout` artifact; model
response text appears in Codex `agent_message` items, not the wrapper's
`events.jsonl`. See the [harness guide](../../../../../../script/eval/README.md)
for artifact and exit-code details.

The two narrow rules are adapted from
[engineering guidance](../../../../../engineering.md#pure-typed-decisions) on
pure decisions and its rule against nested `try` statements in one execution
scope. The three short authored Python excerpts are controlled synthetic input
data; they are not a large incident corpus. There is no answer key or scoring
step. This operational smoke cannot establish accuracy, select a strategy or
model, or support quality or resource generalizations.

The separate nonempty instructions request input-only behavior, but do not
establish tool isolation. Codex may expose residual tools and add automatic
context; the
[accepted CLI limitation](../protocol.md#cli-invocation-boundary-and-accepted-limitation)
remains. This smoke does not establish the primary comparison's guarantees,
modify its protocol, or complete the parent [Evaluation](../README.md).
