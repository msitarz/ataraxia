# Supplemental neutral invocation verification

On 2026-11-04 the maintainer authorized one supplemental neutral attempt at
each of none, low, medium, and high, at concurrency one, with no retries or
quota probes. This is a new four-attempt preparation allocation; it does not
reset the historical none 4/4 or total 4/16 accounting. It does not authorize
corpus trials or a complete input freeze.

The exact instruction bytes are in [min.md](preparation/min.md), SHA-256
`e6a735386f908f03c35bbe65be9e786d7c23ab471ce112b6d0b7f6f198be1cdd`.
The exact neutral prompt bytes are in
[neutral-prompt.txt](preparation/neutral/neutral-prompt.txt), SHA-256
`d85762a537347daee213713bf21413e53fd0d0f5054793a41b0d113087438f7c`.
The prompt reads `Return exactly this single word: READY` followed by LF.

Use the system CLI resolved from PATH to
`/usr/local/Caskroom/codex/0.166.0/bin/codex`, version `codex-cli 0.166.0`,
with the `execution-controls-v3` profile and `gpt-6-luna`. Request the default
owned empty external working directory, read-only sandbox, disabled local tools,
ignored user configuration, approval policy never, and the staged instruction
override. The four separate one-call harness runs allow inspection and a stop
before the next dispatch. Each has a 300-second timeout, 10-second cleanup,
1 MiB combined output cap, zero retries, and no quota probes. Retain every
outcome; do not refill failures. Stop all further dispatch on cleanup
uncertainty, unexpected tool activity or access, drift, cancellation, exposure,
or invalid accounting. Execution evidence is staged outside the checkout to
preserve the harness's clean-checkout requirement and then retained separately.

These requested settings and a successful greeting do not establish effective
model or effort, absolute read isolation, or absence of opaque injected
context. Applicable per-effort baselines include the neutral prompt; their
availability depends on observed usage and matching configuration. The previous
7,983-token observation is not a matched baseline for this run. All Evaluation
acceptance criteria remain TODO.

## Observations

Four separate calls ran serially on 2026-11-04 against clean commit
`8c3c93363237b0cbc899315c4b34b933bf875975`, one per effort in the declared
order. All returned `READY` and exit status zero. Each supervisor recorded an
owned process, a reaped direct child, and a final SIGKILL with no target. No
retry or quota probe ran. No tool-call event appeared in the captured streams;
that absence does not prove a tool was unavailable or that hidden context was
isolated. Each stream included the pre-turn code-mode-host-disabled error
allowed by the [protocol](protocol.md); no tool use was observed.

| Requested effort | Input | Cached input | Cache-write input | Output | Reasoning output | Elapsed seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| none | 3,570 | 0 | 0 | 5 | 0 | 4.702 |
| low | 3,568 | 0 | 0 | 5 | 0 | 3.128 |
| medium | 3,570 | 0 | 0 | 5 | 0 | 3.614 |
| high | 3,570 | 0 | 0 | 5 | 0 | 3.452 |

Counts are the corresponding `turn.completed` usage fields, and elapsed time
is supervisor-observed execution through settlement. Complete output is the
reported output total, without adding the reasoning subset again. No cost,
or server-attested model/provider identity or effort was reported. These
four observations consumed the supplemental allocation in full; the original
preparation counts remain unchanged. No further call is authorized.

The observed input counts include the neutral prompt and automatic context; the
two-token difference shows that treating this context as fixed has uncertainty.
These are candidate per-effort measurements for this exact CLI, profile,
instruction and prompt, not independently verified, frozen trial baselines.
Server-side binding, the authenticated runtime tool surface, source
immutability, and separation from private labels and prior answers remain
unverified. Static rendering is not authenticated runtime proof. A successful
greeting establishes acceptance of the requested settings for that invocation
only. It does not by itself establish effective settings or absolute read
isolation. The local session records described below provide additional binding
evidence, not server attestation.

The
[retained evidence](../../../../../output/reviewer-evaluation/invocation-verification-001/)
contains the raw stdout, stderr and instruction bytes, plus sanitized plan, run
and attempt records. Local repository, output and owned-workspace paths were
replaced with placeholders in JSON; the system CLI path is retained.
`digests.json` records hashes of both original and retained bytes, so sanitized
JSON is not represented as the original. Raw output contains the complete
observable event stream, including the pre-turn notice and usage. Each run's
input snapshot and requested controls are retained. The no-call dry run reported
four calls, approximately eight supplied-context tokens and 50 instruction
tokens per call using `tiktoken` 0.14.0's approximate `o200k_base` model
mapping; the estimates exclude automatic context and framing.

Independent review and a complete freeze, matched binding and baseline review,
and actual boundary verification remain outstanding. This record does not
complete any Evaluation criterion or authorize a scored trial.

## Local runtime metadata

Each returned thread ID identifies a local Codex session file under the native
`sessions/2026/11/04` directory. Only those four session files were inspected.
The retained `session-metadata.json` in each effort directory records the source
basename, whole-file SHA-256, selected line numbers and line hashes, timestamps,
and selected nonsecret fields. Line hashes exclude the terminating LF. Account
identifiers, instructions, unrelated content, and absolute private paths are
not retained. The source files remain untouched.

For each session the local `session_meta` reports provider `openai`, CLI
version `0.166.0`, and source `exec`. The `turn_context` reports model
`gpt-6-luna`, the corresponding requested effort, approval `never`, and a
read-only sandbox. Both recorded working directories equal that attempt's
owned external working directory. The local token-count records match the raw
JSONL usage above and report that output includes reasoning. These records
establish what the local runtime recorded for these sessions; they are not
server attestation of model, provider, effort, or resource isolation.

The original harness outputs remain untouched in a temporary staging directory
on the execution host. They are not a durable repository artifact and may be
removed by normal temporary-file cleanup; retained sanitized records and raw
streams are the durable review evidence. The original and retained digest
manifest permits comparison while the originals remain available.

## Invocation and chronology

From the clean committed checkout, the four actual invocations used the same
command below, with `EFFORT` and `OUTPUT` replaced by the corresponding values
in the table. The temporary output parent was created before execution. This
is a record of the completed calls, not permission to rerun them.

```sh
make eval CLI_ARGS='-d doc/feat/reviewer/engineering/evaluation/preparation/neutral -i doc/feat/reviewer/engineering/evaluation/preparation/min.md -m gpt-6-luna -e EFFORT -c 1 --timeout-seconds 300 --cleanup-timeout-seconds 10 --output-limit-bytes 1048576 --retry-limit 0 --capacity-retry-limit 0 -o OUTPUT'
```

| Effort | Output directory name | Start UTC | End UTC |
| --- | --- | --- | --- |
| none | `none` | 08:27:40.072881 | 08:27:44.774811 |
| low | `low` | 08:27:57.634285 | 08:28:00.762540 |
| medium | `medium` | 08:28:12.837162 | 08:28:16.451406 |
| high | `high` | 08:28:28.767314 | 08:28:32.219859 |

The paths in the retained records use `<run-output>` for each original output
directory, `<repository>` for the checkout, and `<owned-empty-workspace>` for
its invocation cwd. Times are supervisor timestamps on 2026-11-04.
