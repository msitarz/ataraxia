# Bounded CLI preparation

This record covers the authorized, non-live preparation increment for the
[comparison protocol](protocol.md). It does not change the Evaluation's
acceptance criteria or authorize fixtures, corpus trials, or production
reviewer delivery. No model request was made, so there are no observed usage
totals or neutral-call JSONL.

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
Omission does not establish that `none` is unsupported. Strict configuration
parsing accepted `model_reasoning_effort="none"`; no model request checked
runtime acceptance or effective effort. The [OpenAI Configuration
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

No live calls were made. The preparation allowance is 16 neutral calls total,
at most four per effort; 0/16 calls were used. All runtime-effective effort
and usage remain unknown; all Evaluation acceptance criteria remain TODO.

| Effort | Neutral calls | Runtime-effective effort | Usage |
| --- | ---: | --- | --- |
| none | 0/4 | unknown; strict parse accepted, catalog omitted | unknown / not started |
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

## Stopping point

The proposed command in
[`protocol.md`](protocol.md) is not run: an empty directory and read-only
sandbox do not establish input-only operation. The exposed declaration and
inherited context fail the current no-tool/minimal-context gate. No live runner
was built because the supported non-live surfaces already show that the
candidate does not pass that gate. Any later capture method must follow the
protocol's bounds and retain raw output and only usage metadata actually
returned. This is a blocked preparation result, not successful telemetry
preparation, and does not complete any Evaluation criterion.
