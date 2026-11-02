# Evaluation harness

## Examples

From the repository root, prepare the locked environment once:

```sh
make setup
```

You need `uv`, Git, and the Codex CLI on `PATH`, with an authenticated Codex
subscription session. The harness calls Codex CLI; it has no direct provider
API implementation.

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
directory; the harness does not resume a previous run.

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
- The harness requests Codex's read-only sandbox. It cannot establish the
  effective tool set or isolate context that Codex itself may add; its
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
  process work. Infrastructure retry and capacity retry allowances are
  separate.
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
- Progress is best effort: terminal output updates in place; redirected output
  uses newline-delimited updates. Quiet mode suppresses progress, not errors.
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
