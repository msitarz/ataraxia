# Bounded CLI preparation

This record covers bounded preparation for the
[comparison protocol](protocol.md). It does not change the Evaluation's
acceptance criteria or authorize fixtures, corpus trials, or production
reviewer delivery. The maintainer confirms that `gpt-6-luna` supports `none`.
Four authorized neutral CLI invocations were made. The first two were refused
because the external working directory was not trusted. The third failed
during local app-server initialization with `Operation not permitted`, before
model dispatch. The fourth returned the requested neutral greeting under
`gpt-6-luna` with reasoning effort `none`, confirming acceptance for that
invocation. It returned 7,983 input tokens and 15 output tokens; server-internal
binding details remain unavailable.

## Proposed neutral inputs

The proposed fixed instruction and neutral task are nonempty and contain no
corpus material:

- [`min.md`](preparation/min.md), SHA-256
  `e6a735386f908f03c35bbe65be9e786d7c23ab471ce112b6d0b7f6f198be1cdd`.
- [`neutral-prompt.txt`](preparation/neutral-prompt.txt), SHA-256
  `d85762a537347daee213713bf21413e53fd0d0f5054793a41b0d113087438f7c`.

The proposed task is exactly `Return exactly this single word: READY`. These
are review inputs only; they are not frozen for any trial. The requested word
cannot establish tool isolation.

## Non-live CLI findings

The installed CLI reported version `0.164.0`. Its bundled catalog lists
`low`, `medium`, `high`, `xhigh`, and `max` for `gpt-6-luna`, but omits `none`.
This unchanged bundled catalog is an older CLI artifact; its omission does not
override the maintainer's direct confirmation that `none` is supported. Strict
configuration parsing accepted `model_reasoning_effort="none"`. The successful
neutral response in attempt 04 confirms acceptance of the requested `none`
setting for that invocation. The response did not expose server-internal model
binding or effective-setting telemetry. The [OpenAI Configuration
Reference](https://learn.chatgpt.com/docs/config-file/config-reference)
documents the candidate's relevant instruction, shell, and memory settings,
and states that a user opt-out of `features.unified_exec` is ignored. That
reference does not establish the actual rendered context or tool boundary.

The candidate's feature listing reported these flags false: `apps`,
`artifact`, `browser_use`, `browser_use_external`, `code_mode_host`,
`computer_use`, `image_generation`, `in_app_browser`, `multi_agent`,
`plugins`, `shell_tool`, `skill_search`, and `view_image`. Strict parsing
reported CLI/app-server version `0.164.0` with no additional config
requirements. Exact non-secret outputs are retained in
[`codex-version.txt`](preparation/evidence/codex-version.txt),
[`model-catalog-gpt-6-luna.json`](preparation/evidence/model-catalog-gpt-6-luna.json),
[`effective-features.txt`](preparation/evidence/effective-features.txt), and
[`strict-config-validation.json`](preparation/evidence/strict-config-validation.json).

The supported `codex debug prompt-input` render retained an `additional_tools`
declaration that includes `functions.exec`, `functions.wait`, and `clock.sleep`.
The full declaration is in
[`tool-declarations.json`](preparation/evidence/tool-declarations.json), and the
complete rendered prompt input is in
[`prompt-input.json`](preparation/evidence/prompt-input.json). The
`functions.exec` description is a JavaScript tool orchestrator; the explicit
declaration excerpt lists `apply_patch` and MCP resource readers. Its generic
example mentions `exec_command`, but this diagnostic does not establish that
`exec_command` or those nested readers are available in an authenticated live
invocation. The visible declaration itself violates the protocol's no-tool gate.
This is evidence about the non-live debug render only, not a claim about
universal CLI behavior or actual live file access.

The render also included developer permission and collaboration-mode messages
and a user environment bundle. It showed no project `AGENTS.md`, skill,
memory, or prior-answer message. The inherited developer and environment
messages exceed the proposed minimal context. This diagnostic used an empty
`CODEX_HOME` and an external working directory, so authenticated invocation
context remains unverified. No authentication file, token, or header was read
or retained.

## Effort status

The preparation allowance is 16 neutral calls total, at most four per effort.
All four none attempts were used, leaving 12/16 total attempts for other
efforts. Three attempts produced no model response; attempt 04 returned a
neutral response and usage telemetry.
The prior maintainer-reported baseline of 7,380 `input_tokens` for a separate
none/greeting invocation remains reported, not independently captured here.
Attempt 04's successful response confirms the requested `none` effort was
accepted for that invocation. The stream does not expose server-internal model
binding. All Evaluation acceptance criteria remain TODO.

| Effort | Neutral calls | Runtime-effective effort | Usage |
| --- | ---: | --- | --- |
| none | 4/4 attempts; 1 response | requested effort accepted for attempt 04; internal binding unknown | attempt 04: 7,983 input, 0 cached input, 0 cache-write input, 15 output, 0 reasoning tokens; prior 7,380-token baseline is maintainer-reported |
| low | 0/4 | unknown / not started | unknown / not started |
| medium | 0/4 | unknown / not started | unknown / not started |
| high (`hard`) | 0/4 | unknown / not started | unknown / not started |

## Diagnostic provenance

The CLI evidence was rendered from source revision
`743d69845fe5bffa0e3fe93c580fada0c8e45ae4` using the pinned installation
identified in [`codex-version.txt`](preparation/evidence/codex-version.txt).
The exact prompt-input invocation, cwd, and explicit environment are
reconstructed from the tool call; the shell command was not separately logged
by a recorder. Its exit status was 0. The command is retained here so the
non-live diagnostic can be reproduced:

```sh
CODEX_HOME=/private/tmp/ataraxia-reviewer-preflight-codex-home \
codex debug prompt-input \
  -c 'model="gpt-6-luna"' \
  -c 'model_reasoning_effort="none"' \
  -c 'model_instructions_file="/private/tmp/ataraxia-reviewer-preflight/doc/feat/reviewer/engineering/evaluation/preparation/min.md"' \
  -c 'skills.bundled.enabled=false' \
  -c 'tools.experimental_request_user_input.enabled=false' \
  -c 'memories.use_memories=false' \
  -c 'agents.enabled=false' \
  -c 'features.multi_agent=false' \
  -c 'features.shell_tool=false' \
  -c 'web_search="disabled"' \
  --disable apps --disable artifact --disable browser_use \
  --disable browser_use_external --disable code_mode_host \
  --disable computer_use --disable image_generation \
  --disable in_app_browser --disable plugins --disable skill_search \
  --disable view_image \
  'Return exactly this single word: READY' \
  > /private/tmp/ataraxia-reviewer-preflight-evidence/prompt-input.json
```

The command ran in `/private/tmp/ataraxia-reviewer-preflight-codex-home`, an
empty temporary directory also used as `CODEX_HOME`. The CLI version, bundled
model catalog, effective feature listing, and strict-config output were
captured by separate read-only commands with exit status 0. Their original
argv was not independently recorded. The retained evidence hashes are:

| Evidence | SHA-256 |
| --- | --- |
| [`prompt-input.json`](preparation/evidence/prompt-input.json) | `e138ed1945d291b220236a931e38c1d64d899dbcef3970e702e5af293a9653f1` |
| [`tool-declarations.json`](preparation/evidence/tool-declarations.json) | `2456830e28448b52faca85d819f5e2f241c4395a00a141c0cdf48d8154de4d89` |
| [`codex-version.txt`](preparation/evidence/codex-version.txt) | `1c27284b7f5c74467a59a96821de67dc184c09423d800257b4f2e8eb3b1445a6` |
| [`model-catalog-gpt-6-luna.json`](preparation/evidence/model-catalog-gpt-6-luna.json) | `83a1998a20b59ddde30e7ab9e51d5303b65e37c8c6ccda97e3abfd8c94ef7600` |
| [`effective-features.txt`](preparation/evidence/effective-features.txt) | `63189233e42b492471eaef5925de6c739cab1908c4fb7351460aeff6327f4b94` |
| [`strict-config-validation.json`](preparation/evidence/strict-config-validation.json) | `9fc2ef439d8c02d0e8a81da1060db3223bb8bba1a84dcac3d0db207f41392019` |

The rendering did not include a source timestamp, and the original shell call
did not record capture time. File modification times reflect copying into this
worktree, not observation time.

## Live attempt and stopping point

All four attempts used the unchanged greeting and exact reviewed `min.md` bytes
from an external temporary working directory. The standard-library capture
supervisors were configured for a 300-second deadline, 10-second cleanup, 1 MiB
combined output cap, and concurrency one; these configured bounds are recorded
with each attempt. The source used for attempts 01-02 is retained in
[`probe-supervisor-attempts-01-02.py.txt`](preparation/evidence/probe-supervisor-attempts-01-02.py.txt).
The exact argv, cwd, UTC and monotonic timing, exit status, prompt and
instruction digests, stdout, and stderr for each attempt are retained in the
[`attempt 01 evidence`](preparation/evidence/live-none-attempt-01-invocation.json)
and
[`attempt 02 evidence`](preparation/evidence/live-none-attempt-02-invocation.json).
Both commands exited with status 1 before any model request and reported
`Not inside a trusted directory and --skip-git-repo-check was not specified.`
Both used the same argv without that flag; the second was intended to add it,
but the supervisor's argv remained unchanged. Attempt 03 used the reviewed
`--skip-git-repo-check` flag, but local app-server initialization failed with
`Operation not permitted` before a model response. Its raw stderr and empty
JSONL stdout are retained in the
[`attempt 03 evidence`](preparation/evidence/live-none-attempt-03-invocation.json).
The supervisor recorded `exit_status: null`, `cleanup_complete: false`, and a
process-group `PermissionError`. A later elevated inspection found no matching
leader or process-group member. The original exit status remains unavailable;
the follow-up is retained separately in
[`attempt 03 cleanup follow-up`](preparation/evidence/live-none-attempt-03-cleanup-followup.json).

Attempt 04 ran the reviewed command through the supervisor with elevated
permissions. The JSONL stream contains a neutral greeting and a completed-turn
usage record. It reports 7,983 `input_tokens`, zero cached and cache-write
input tokens, 15 `output_tokens`, and zero `reasoning_output_tokens`; no cost
field or server-internal model binding was returned. The stream contains no
tool-call event, which does not establish input-only isolation. The raw
response is retained in
[`attempt 04 stdout`](preparation/evidence/live-none-attempt-04-stdout.jsonl)
with its
[`invocation record`](preparation/evidence/live-none-attempt-04-invocation.json)
and stderr. The supervisor again recorded `cleanup_complete: false` and a
process-group `PermissionError`. Although attempt 04 was dispatched with
elevated permissions, that cleanup call still failed. Later elevated checks
found neither PID/PGID 94280 nor any process-group member. That follow-up is
retained in
[`attempt 04 cleanup follow-up`](preparation/evidence/live-none-attempt-04-cleanup-followup.json);
the leader's exit status could not be reconstructed. No further launch was
made. Hard token/context caps remain unknown; the 32,000-token planning cap is
not a runtime-enforced limit.

The fourth-attempt supervisor and argv are retained in
[`probe-supervisor-attempt-04.py.txt`](preparation/evidence/probe-supervisor-attempt-04.py.txt)
and [`attempt 04 plan`](preparation/evidence/live-none-attempt-04-plan.json).
The plan asserts the required `--skip-git-repo-check`, exactly one `none`
setting, and exactly one unchanged greeting. The supervisor requires both
`--launch` and `--authorized`, records process ID and group ID, applies a
300-second deadline independent of leader exit, and configures process-group
termination and leader reaping for the 10-second cleanup window. Cleanup
attempts 03 and 04 recorded `PermissionError`; later elevated checks found no
remaining processes in either group.

Attempts 01-03 met the protocol's infrastructure stop condition. The owner
separately authorized attempt 04 as an elevated final recovery for the
maintainer-requested neutral support check, within the original four-call
per-effort allowance. This is a retained preparation deviation; it does not
change the trial stop rule or authorize corpus trials.

The prior debug render still fails the input-only gate. A successful neutral
greeting would not establish tool isolation or production readiness. No corpus
trial, fixture, harness, or Evaluation completion is authorized by this
preparation record.
