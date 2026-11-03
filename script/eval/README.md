# Evaluation harness

## Examples

From the repository root, prepare the locked environment once:

```sh
make setup
```

You need Python 3.14 or newer, `uv`, Git, and the Codex CLI on `PATH`, with an
authenticated Codex subscription session for execution. Setup installs the
locked development dependencies.

### Disabled-tool smoke example

This separate two-call example asks the model to run a fixed `printf` command
and list only its current directory's names. Its own instructions file
intentionally permits those harmless tool requests; the supplied reviewer
smoke below continues to request no tools.

Choose a fresh persistent output path and create only its parent:

```sh
mkdir -p "$HOME/ataraxia-eval-results"
```

Preview the two calls:

```sh
uv run --no-sync python -m script.eval \
  -d script/eval/example/tool-disable/requests \
  -i script/eval/example/tool-disable/instructions.md \
  -m gpt-6-luna -e low -c 1 \
  --timeout-seconds 120 --cleanup-timeout-seconds 10 \
  --output-limit-bytes 65536 --retry-limit 0 --capacity-retry-limit 0 \
  -o "$HOME/ataraxia-eval-results/tool-disable-001" -n
```

Then run the same command without its final `-n` to make exactly two calls.
The output directory must be new; choose another name if it already exists.

Do not enable tools to silence a warning. Keep emitted error items, including a
code-mode-host disabled item that can appear before a normal response. Inspect
each raw attempt's `stdout` JSONL and `run.json` for the invocation controls,
working directory, and observed tool events; response text alone is not evidence
of execution or blocking.

Interpret the observations cautiously:

- No callable tool offered means **tool unavailable**.
- An attempted call explicitly denied in the runtime trace means **observed
  attempt denied**.
- Any requested operation that actually runs is a **boundary failure** for a
  disabled-tool profile.
- A refusal, model self-report, or absence of tool events alone is
  **inconclusive**; no events can also mean the model refused or chose not to
  attempt a tool.

An empty working directory does not provide absolute read isolation. The example
demonstrates requests under a disabled-tool profile; it does not prove that all
tools are blocked until observations support that conclusion. It is not a
reviewer-quality evaluation.

### Supplied reviewer smoke example

Start from a clean repository root. Choose a fresh persistent output path and
create only its parent:

```sh
mkdir -p "$HOME/ataraxia-eval-results"
```

Preview the full example matrix first. This dry run does not start Codex or
create output:

```sh
uv run --no-sync python -m script.eval \
  -d script/eval/example/rules \
  -d script/eval/example/sources \
  -i script/eval/example/instructions.md \
  -m gpt-6-luna -e none -e low -c 1 \
  --timeout-seconds 120 --cleanup-timeout-seconds 10 \
  --output-limit-bytes 65536 --retry-limit 0 --capacity-retry-limit 0 \
  -o "$HOME/ataraxia-eval-results/reviewer-smoke12-001" -n
```

Confirm it reports 12 calls, then run the same command without `-n`. The
output directory must be new; choose another name if it already exists.

The matrix contains two rule files, three synthetic source files, one model,
and two efforts: 12 calls. The rule file comes first, followed by the source
file, joined by two LF characters.

- Each call has one harness attempt; retry limits are zero and quota waiting
  is off.
- The 12 calls exclude Codex's internal retries and the harness's local Codex
  version query.
- The dry run makes no model call and may download tokenizer vocabulary on
  first use.
- Retain failed and interrupted attempts; do not automatically rerun them.
- Inspect `plan.json`, `run.json`, `events.jsonl`, and per-attempt records under
  `attempts/`. Attempt `.stdout` files contain raw Codex JSONL; response text
  appears in `agent_message` items, not in `events.jsonl`.
- The two rule prompts adapt
  [pure-decision and nested-`try` guidance](../../doc/engineering.md#pure-typed-decisions)
  from source revision `25958a82242e4c89a269cbd5c8f1b4d43543b234`.
- The three Python excerpts are controlled synthetic inputs. There is no
  answer key or scoring, so the smoke cannot establish accuracy or support
  model, strategy, quality, or resource conclusions.
- The instructions request input-only behavior, but the
  [accepted CLI limitation](../../doc/feat/reviewer/engineering/evaluation/protocol.md#cli-invocation-boundary-and-accepted-limitation)
  remains; this smoke does not establish tool isolation or change the primary
  comparison protocol.

### Compose your own inputs

Preview a small matrix without making model calls or creating output:

```sh
make eval CLI_ARGS='-d path/to/contexts -m gpt-6-luna -e low -n'
```

The same CLI can be run directly from a terminal or scheduler:

```sh
uv run --no-sync python -m script.eval -d path/to/contexts -m gpt-6-luna -e low -n
```

For execution, supply a fresh output directory:

```sh
make eval CLI_ARGS='-d path/to/rules -d path/to/examples -m gpt-6-luna -e low -c 6 -o /tmp/eval-run-001'
```

Each directory contributes one immediate regular file per composed context.
With two files in each directory, two models, and two efforts, there are
`2 × 2 × 2 × 2 = 16` calls. For the first context selection, call order is:

| Context | Model | Effort |
| --- | --- | --- |
| rules/a + examples/x | gpt-6-luna | low |
| rules/a + examples/x | gpt-6-luna | medium |
| rules/a + examples/x | gpt-6.1-sol | low |
| rules/a + examples/x | gpt-6.1-sol | medium |

The last directory varies fastest while forming context selections. For each
selection, models and then efforts follow their argument order, with effort
varying fastest. Repeated `-d`, `-m`, and `-e` options request the full product.

Use `-s` between adjacent directories to choose their join text. This example
passes literal `\n` escapes through Make, which the harness decodes as newline
bytes:

```sh
make eval CLI_ARGS='-d path/to/rules -s \n---\n -d path/to/examples -m gpt-6-luna -e low -n'
```

Without `-s`, the join is two LF characters. Supported escapes are `\n`,
`\r`, `\t`, and `\\`.

An optional `-i path/to/instructions.txt` supplies Codex's
`model_instructions_file` setting. It replaces Codex's default system
instructions; directory files remain ordinary supplied context.

Quota waiting and capacity retries are optional. Quota waiting can use a
duration limit and a count of quota-probe CLI invocations:

```sh
make eval CLI_ARGS='-d path/to/contexts -m gpt-6-luna -e low -o /tmp/eval-run-002 --wait-for-quota --quota-wait-limit-seconds 1800 --quota-probe-budget 3'
```

Capacity retries have a separate allowance from infrastructure retries and
require backoff durations, such as
`--capacity-retry-limit 1 --capacity-backoff-base-seconds 30
--capacity-backoff-cap-seconds 60`. Quota waiting is off by default, as are
capacity retries.

Every invocation requires at least one `-d`, `-m`, and `-e`. Execution also
requires `-o` naming a new output directory. Rerun a subset with another new
directory; the harness does not resume a previous run. A sparse subset that is
not one Cartesian product requires separate invocations and fresh output
directories. The caller reconciles previous attempts and retries against its
experiment limits across runs. Count reruns or cached answers as independent
trials only when the caller’s protocol permits it; the harness does not know
that protocol or enforce its budgets.

## Responsibilities

- The harness validates and freezes supplied files, composes contexts, expands
  the requested model and effort matrix, runs Codex CLI calls, and records
  execution evidence.
- It knows **nothing** about evaluation protocols, rules, labels, expected
  answers, or scoring. Separate preparation tools and the caller provide
  context files and settings, then interpret, validate, and score artifacts.
- It does not set an experiment's block order or repetitions.
- Calls use Codex CLI and its subscription session. There is no direct provider
  API implementation.
- When quota waiting is enabled, the harness reads local session metadata for
  the active invocation only. It does not read unrelated session history,
  authentication files, or personal configuration itself. Codex CLI still
  applies its own settings and context.
- Quota telemetry requires Codex CLI 0.164.0 or later and a recognized,
  validated runtime session shape. It fails closed when identity, freshness,
  completeness, or quota scope cannot be verified.
- Execution requests Codex's read-only sandbox and `approval_policy="never"`,
  using `--ignore-user-config`. Controlled tests exercise the local invocation,
  not live authentication or provider availability. The harness cannot establish
  the effective tool set or isolate context that Codex itself may add; its
  invocation controls do not prove tool-free execution or personal-context
  isolation.

## Inputs and limits

- Inputs must be within one Git repository whose tracked and untracked working
  tree is clean. Selected files must be tracked regular files, not symbolic
  links. Directory selection is immediate, non-recursive, and lexical.
- The harness freezes input bytes before dispatch. Each context combines one
  selected file from each directory in argument order. Repeated directories
  remain separate positions.
- `-c` limits concurrent attempts. Per-attempt and cleanup timeouts bound
  process work. An output limit of zero disables the byte cap, so capture memory
  is unbounded despite the timeouts. Infrastructure retry and capacity retry
  allowances are separate.
- Quota waiting is opt-in. A supplied wait-duration limit bounds total waiting;
  if omitted, the harness sets no cumulative duration bound. The optional
  `--quota-probe-budget` counts separate quota-check CLI invocations. Neither
  option is a money or token budget.
- Token estimates cover supplied context only. They exclude automatic CLI and
  system context; a configured instructions file is estimated separately.
  Estimates are informational and enforce no token or monetary budget. Codex
  may retry requests within one CLI invocation, and those retries are not
  counted as harness attempts. Other sessions can share the subscription
  quota.
- Output may be inside or outside the repository. If it is inside and not
  ignored by Git, it leaves untracked files and makes the checkout dirty.
- Dry run lists every scheduled position, source path, model, effort, and token
  estimate, with totals and estimation caveats. Instructions are estimated
  separately. It validates and freezes inputs, but does not start Codex or
  create harness output. A first tokenizer lookup may download and cache
  vocabulary data.

For example, one dry-run row can look like:

```text
  0: model=gpt-6-luna effort=low context tokens=42
    source: 'contexts/example.txt'
```

## Artifacts and control

- `plan.json` records the frozen plan; `instructions.bin` is present when an
  instructions file was supplied.
- Per-call attempt directories under `attempts/` retain process records and
  raw stdout and stderr. `events.jsonl` records lifecycle events, and `run.json`
  summarizes the run. Opt-in quota probes also leave evidence.
- These files are execution evidence. The harness does not turn them into a
  scored evaluation report.
- Progress is best effort. A capable terminal replaces a live panel; narrow,
  short, resized, or detailed reports use multiline blocks, as does redirected
  output. Colors supplement labels and respect `NO_COLOR` and `TERM=dumb`.
  Quiet mode suppresses progress, not errors. After execution a short bounded
  drain lets a responsive writer show its final frame. Blocked or partial
  output can lose that frame or arrive after the stdout result.
- The panel separates scheduled calls, attempt invocations, and quota probes.
  Completed calls include successes, failures, and cancellations; remaining
  calls have not settled. Retries are additional attempts, not extra scheduled
  calls. Process success is not a reviewer verdict. Quota values stay unknown
  unless a validated observation supplies them.
- Supported cancellation requests cooperative shutdown and records settled
  evidence when possible. Forced operating-system termination cannot be
  cleaned up by the process.
- Standalone shell scripts or schedulers can launch the CLI; no agent
  conversation or installed scheduler service is required.
- Exit codes: `0` success; `1` failed run or invalid prerequisites; `2` invalid
  arguments; `3` incomplete run (including quota telemetry) or evidence
  setup/recording; `130` cancellation.

For the full option list, run `make eval CLI_ARGS='--help'` or
`uv run --no-sync python -m script.eval --help`.

For example, a running panel can include:

```text
Run: 5a9a9c88-0753-4423-a62c-b30601c90001
Status: running — This is execution status, not a verdict.
Calls
  Completed: 11 — Includes failed and cancelled calls.
  Succeeded: 11 — Processes completed successfully.
  Failed: 0 — Calls settled unsuccessfully.
  Cancelled: 0 — Calls ended by cancellation.
  Remaining: 1 — Calls not yet settled.
Attempts
  Started: 12 — Attempt invocations dispatched.
  Active: 1 — Attempts still in progress.
  Retries: 0 — Additional attempts dispatched.
Quota probes
  Started: 0 — Separate quota checks dispatched.
Quota: unknown — No validated observation is available.
```

## Top-level architecture

```text
ordered inputs + settings
          │
          ▼
validate Git inputs and freeze bytes
          │
          ▼
compose contexts and schedule model/effort matrix
          ├──────────────► dry run: call count + estimates, then exit
          │
          ▼
bounded coordinator ─────► Codex CLI process supervisor
          │                              │
          └──────── evidence store ◄─────┘
                         │
                         ▼
                  output directory
```

The CLI parses settings; input handling snapshots files; the planner composes
contexts and schedules calls. The coordinator applies concurrency, timeout,
retry, and optional quota-wait policy. The existing process supervisor owns
process acquisition, capture, and cleanup. The evidence adapter persists the
plan and observed outcomes. Token estimation is a dry-run report step, separate
from dispatch policy.

For implementation detail, see the [CLI](cli.py), [input reader](inputs.py),
[planner](plan.py), [coordinator](runner/coordinator/coordinator.py),
[Codex adapter](runner/adapters/codex.py), [evidence store](evidence.py),
[token estimator](tokens.py),
[harness architecture](../../doc/feat/reviewer/engineering/evaluation/evaluation-harness/architecture.md),
and
[process supervisor guidance](../../doc/feat/reviewer/engineering/evaluation/process-supervisor/README.md).
