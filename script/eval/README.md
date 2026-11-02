# Evaluation harness

## Examples

From the repository root, prepare the locked environment once:

```sh
make setup
```

You need `uv`, Git, and the Codex CLI available on `PATH`, with an authenticated
Codex subscription session. The harness invokes the CLI; it does not implement
direct provider API calls.

Preview the smallest matrix without making model calls or creating output:

```sh
make eval CLI_ARGS='-d path/to/contexts -m gpt-6-luna -e low -n'
```

For a real run, give it a fresh output directory:

```sh
make eval CLI_ARGS='-d path/to/rules -d path/to/examples -m gpt-6-luna -e low -c 6 -o /tmp/eval-run-001'
```

Each directory contributes one immediate regular file per composed context.
With two files in each directory, two models, and two efforts, the harness
schedules `2 × 2 × 2 × 2 = 16` calls:

| Context selection order | Model | Effort |
| --- | --- | --- |
| rules/a + examples/x | gpt-6-luna | low |
| rules/a + examples/x | gpt-6-luna | medium |
| rules/a + examples/x | gpt-6.1-sol | low |
| rules/a + examples/x | gpt-6.1-sol | medium |
| rules/a + examples/y | gpt-6-luna | low |
| … | … | … |

The final directory varies fastest, followed by model and effort in their
argument order. The complete context product is followed by each model and
effort combination. Add repeated options to request the full product:

```sh
make eval CLI_ARGS='-d path/to/rules -d path/to/examples -m gpt-6-luna -m gpt-6.1-sol -e low -e medium -c 6 -o /tmp/eval-run-001'
```

Use `-s` between adjacent directories to set their join text. For example,
`-s \n---\n` inserts a newline, marker, and newline between the selected
files; without `-s`, the join is two LF characters. The supported escapes are
`\n`, `\r`, `\t`, and `\\`.

An optional `-i path/to/instructions.txt` supplies a separate Codex
`model_instructions_file`. It replaces Codex's default system instructions;
directory files remain ordinary supplied context.

Quota waiting and capacity retries are optional controls. For example, quota
waiting can be enabled with a bounded wait and a count of quota-probe CLI
invocations:

```sh
make eval CLI_ARGS='-d path/to/contexts -m gpt-6-luna -e low -o /tmp/eval-run-002 --wait-for-quota --quota-wait-limit-seconds 1800 --quota-probe-budget 3'
```

Capacity retry allowances are separate from infrastructure retry allowances
and also require backoff durations, for example
`--capacity-retry-limit 1 --capacity-backoff-base-seconds 30
--capacity-backoff-cap-seconds 60`. Quota waiting is off by default, and the
capacity retry allowance defaults to zero.

Every invocation requires at least one `-d`, `-m`, and `-e`. `-o` is required
for execution and must name a new output directory. Re-run a subset with a new
output directory; the harness does not resume or overwrite a prior run.

## What the harness does

The harness accepts context directories and run settings, composes ordered
contexts, expands them over the requested model and reasoning-effort matrix,
and runs each call through Codex CLI. It retains the plan, inputs, process
observations, and run summary in the chosen output directory.

It knows **nothing** about an evaluation protocol, rules, labels, expected
answers, or scoring. Separate preparation tools and the caller supply suitable
context files and configuration, then interpret, validate, and score the
resulting artifacts. The harness does not own those steps or impose an
experiment's order, repetitions, or budgets.

All calls currently use Codex CLI and its subscription session. There is no
direct provider API implementation. The harness does not read personal
configuration, authentication files, or session history. Optional quota
telemetry is limited to the active invocation's supported local Codex session
data; support currently recognizes the Codex CLI 0.164.0 session shape and
fails closed when required identity, freshness, completeness, or scope cannot
be established. Recognition may need updating as the CLI changes.

## Inputs and execution limits

- Inputs must be inside one Git repository with a clean tracked and untracked
  working tree. Selected files must be tracked, regular, non-symbolic-link
  files; directory selection is immediate and non-recursive, in lexical file
  order.
- The harness freezes input bytes before dispatch and composes one selected
  file from each directory in argument order. Repeated directories remain
  distinct positions. Each directory boundary defaults to two LF bytes or
  uses its corresponding `-s` value.
- `-c` limits concurrent attempts. Per-attempt timeout and cleanup timeout
  bound process work. Infrastructure retry allowances and capacity retry
  allowances are separate controls.
- Optional quota waiting has a cumulative wait-duration limit. Its
  `--quota-probe-budget` counts separate quota-check CLI invocations. It is not
  a money or token budget.
- Token estimates describe supplied context only and are informational. They
  do not enforce a token or monetary budget. Codex may retry requests within
  one CLI invocation; those internal retries are not counted as harness
  attempts. Other sessions can share and consume the same subscription quota.
- The output directory can be inside or outside the repository. A new output
  directory inside the repository creates untracked files and makes the
  working tree dirty for a later run.
- Dry run validates and displays the planned matrix and informational token
  estimates. It does not start Codex or create output. A first token-estimator
  lookup may download and cache tokenizer data.

## Artifacts and control

The output directory contains a frozen `plan.json`, optional staged
`instructions.bin`, per-call attempt directories under `attempts/`, an
append-only `events.jsonl`, and a final `run.json`. Raw stdout and stderr and
process lifecycle records are retained with attempt evidence. Quota probes,
when enabled, also leave evidence. This is execution evidence, not a scored
evaluation report.

Progress is best effort: terminal runs update in place, while redirected output
uses newline-delimited updates. Quiet mode suppresses progress, but errors are
still reported. On supported cancellation signals, the harness requests
cooperative shutdown and records settled evidence when possible; forced
termination by the operating system cannot be cleaned up by the process.
Standalone shell scripts or schedulers can launch the CLI; no agent
conversation or installed scheduler service is required. Exit codes are `0`
for success, `1` for run failure, `2` for invalid arguments, `3` when evidence
setup or recording is incomplete, and `130` for cancellation.

## Top-level architecture

```text
ordered inputs + CLI settings
          │
          ▼
validate Git inputs and freeze bytes ──► optional token estimates
          │
          ▼
compose ordered contexts and model/effort matrix
          │
          ▼
bounded async coordinator ──► Codex CLI process supervisor
          │                              │
          └──────── evidence store ◄─────┘
                         │
                         ▼
                output directory
```

The CLI parses settings; input handling validates and snapshots files; the
planner composes contexts and schedules calls; the coordinator applies
concurrency, timeout, retry, and optional quota-wait policy. The existing
process supervisor owns process acquisition, capture, and cleanup. The
evidence adapter persists the plan and observed outcomes. Token estimation is
informational and separate from dispatch policy.

For implementation boundaries and lower-level flow, see the
[harness architecture](../../doc/feat/reviewer/engineering/evaluation/evaluation-harness/architecture.md),
[process supervisor guidance](../../doc/feat/reviewer/engineering/evaluation/process-supervisor/README.md),
and the [current system architecture](../../doc/architecture.md).
