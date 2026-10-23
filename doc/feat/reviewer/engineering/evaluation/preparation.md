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

**Current Step 1 status: maintainer-accepted known issue; boundary unverified.**
The maintainer decided to continue with `codex exec`, accepting the remaining
tool declarations and injected permission, collaboration, and environment
context, and to subtract measured configuration-specific input baselines in
final reporting. The combined fourth static candidate still declares
`functions.exec`/`functions.wait`, MCP resource readers, and `apply_patch`.
Their presence alone no longer blocks preparation. This is acceptance of a
limitation, not verified tool-free operation or authenticated runtime isolation.
Attempt 04 confirmed requested `none` effort support for that invocation only.

The
[protocol's CLI boundary and accounting rules](protocol.md#cli-invocation-boundary-and-accepted-limitation)
retain immutable-input, read-only-source, withheld-label and prior-answer
separation, bounded-resource, and failure/stop protections. Token subtraction
cannot undo possible tool/context influence on judgments. Other preparation
requirements remain unresolved; neither all bounded preparation nor the
Evaluation is complete. All acceptance criteria remain TODO. No additional
calls, fixtures, wrapper implementation, corpus trials, or production delivery
are authorized by this amendment.

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
invocation. The visible declaration failed the former no-tool gate; the
maintainer now accepts its presence as the known limitation above. This is
evidence about the non-live debug render only, not a claim about universal CLI
behavior or actual live file access.

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

The prior debug render retains the accepted tool/context limitation. A
successful neutral greeting does not establish tool isolation or production
readiness. No corpus trial, fixture, harness, or Evaluation completion is
authorized by this
preparation record.

## Follow-up non-live tool-surface investigation

On 2026-10-23, the supported `codex debug prompt-input` renderer was checked
against the official
[Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)
for code-mode namespace controls. The reference documents
`features.code_mode.excluded_tool_namespaces` as excluding namespaces from
nested code-mode guidance and executor exposure, and
`features.code_mode.direct_only_tool_namespaces` as requiring direct calls for
those namespaces. This describes nested code-mode exposure; it does not promise
removal of the outer `functions.exec` wrapper or other host-provided context.

Two read-only render candidates used the unchanged `min.md` bytes, neutral
`READY` prompt, `gpt-6-luna`, and requested `medium` effort, with an empty
temporary `CODEX_HOME`:

1. `features.code_mode.enabled=false`,
   `features.code_mode.excluded_tool_namespaces=["functions"]`,
   `features.multi_agent=false`, `features.shell_tool=false`,
   `features.apps=false`, `features.plugins=false`,
   `skills.bundled.enabled=false`, `memories.use_memories=false`, and
   `agents.enabled=false`, plus the existing browser, computer, image, and
   skill-search feature disables. The exact raw render is
   [`prompt-input-code-mode-excluded-functions.json`](preparation/evidence/prompt-input-code-mode-excluded-functions.json),
   SHA-256 `f415de7c324eb704fb1b405759906dbfd5e1ddf53d00d406bf9320ef856a767d`.
2. The same settings with code mode enabled,
   `features.code_mode.excluded_tool_namespaces=["functions", "clock",`
   `"mcp__codex_app"]`,
   and `features.code_mode.direct_only_tool_namespaces=["functions"]`. The
   exact raw render is
   [`prompt-input-code-mode-direct-exclusion.json`](preparation/evidence/prompt-input-code-mode-direct-exclusion.json),
   SHA-256 `3a927988dae213df7c0c21bb265525508a899a853e104b92e406989093095d6e`.

Both rendered outputs still declare the `functions` namespace with `exec`,
`wait`, and request-input functions, and the `clock.sleep` tool. The `exec`
description continues to expose its generic nested-tools mechanism, including
MCP resource readers. Both outputs also retain the developer permission and
collaboration-mode messages and an environment-context block. They show no
project `AGENTS.md`, skill, memory, or prior-answer content for those exact
static renders. The prompt renders do not report effective configuration. A
separate strict startup-config parse and a render with
`features.sleep_tool=false` are recorded below. The reference's scope and
unchanged outer declarations do not establish removal of the outer host wrapper.

The noninteractive `codex exec --help` surface offers no general tool
allowlist/denylist or output of a complete authenticated runtime tool
declaration. No supported candidate established tool-free/input-only operation.
The investigation stopped before another live call; the maintainer has since
accepted that remaining limitation. The retained renders are static diagnostic
evidence, not proof of actual invocation capability or runtime context. No
change to the prior raw artifacts or neutral-call budget is made.

## Pinned app-server controls and offline schemas

The follow-up checked `codex app-server --help`, `codex features list`, and the
installed app-server's supported offline JSON Schema generator. The pinned
feature listing reports `code_mode` as under development and off by default,
`sleep_tool` as stable and on, and `shell_tool`, `multi_agent`, and
`unified_exec` as stable and on. `codex app-server --strict-config
--print-startup-config` accepted `features.code_mode.enabled`, both code-mode
namespace settings, and `features.sleep_tool=false`, exiting 0 and reporting
app-server version `0.164.0`. This establishes parser acceptance only; the
startup-config output does not report an effective tool list.

A third read-only candidate used the same neutral prompt and exact `min.md`
bytes, enabled code mode with the excluded and direct-only namespaces, and set
`features.sleep_tool=false`, `features.shell_tool=false`,
`features.multi_agent=false`, `features.apps=false`,
`features.plugins=false`, `skills.bundled.enabled=false`,
`memories.use_memories=false`, and `agents.enabled=false`, with the same
browser, computer, image, and skill-search disables as the prior candidates.
Its raw render is
[`prompt-input-code-mode-sleep-off.json`](preparation/evidence/prompt-input-code-mode-sleep-off.json),
SHA-256 `21e2ffce44def447e410a5d87fa0709b23329ca92bf16e1d8a3126f524177827`.
That render omits `clock.sleep`, showing the stable sleep feature control in
this diagnostic, while retaining the outer `functions` namespace and its
`exec` and `wait` declarations. This distinguishes removal of a nested tool
from removal of the outer wrapper.

The generated `ThreadStartParams` schema contains caller-provided
`dynamicTools`, instruction, config, environment, model, and policy fields; it
has no general tools property. `TurnStartParams` has input, additional-context,
environment, model, sandbox, policy, and collaboration fields, but no tools or
dynamic-tools property. An empty `dynamicTools` list can express no
caller-supplied custom functions; the schema does not claim it removes Codex's
built-in tools. Empty environment lists disable environment access for the
turn/thread scope described by the schema, not all built-in tools. Nullable
instruction fields and an open-ended `config` object do not, by themselves,
prove all inherited context is absent or that a particular configuration took
effect. No app-server process or RPC was started, so its authenticated runtime
declaration and effective prompt remain unobserved.

The exact commands, schema hashes, inspected fields, and official app-server
documentation references are retained in
[`app-server-start-turn-schema-summary.txt`](preparation/evidence/app-server-start-turn-schema-summary.txt).
The official documentation describes initializing the protocol, starting a
thread, then starting a turn; it does not identify a control that removes all
built-in tools or proves inherited context is absent. This finding is limited to
the inspected CLI 0.164.0 help, configuration parser, generated protocol
schemas, and the cited documentation. It does not establish that no host-level
configuration exists outside these surfaces.

## Combined Step 1 candidate and stopping point

Four distinct static candidate configurations were rendered in this follow-up
within the eight-candidate cap. The exact argv arrays, cwd, explicit
`CODEX_HOME`, input digests, output sizes, and reconstruction limits are
retained in the
[candidate invocation record][candidate-record].
Candidates 01-03 are reconstructed from the recorded tool-call arguments; no
separate argv recorder was running. Their external cwd and `CODEX_HOME` matched,
but emptiness was not verified before those runs. Candidate 04 used a fresh
external cwd and `CODEX_HOME`; `rg --files --hidden` returned no files directly
before the render. The CLI then created installation metadata there. The exact
`min.md` digest was
`e6a735386f908f03c35bbe65be9e786d7c23ab471ce112b6d0b7f6f198be1cdd`. The
exact 38-byte prompt argument digest was
`b0c0ccb73ad2dd6519da8f42c662ddb1677dcdaabbfce50603e196429051b975`.

Candidate 04 combined the already documented settings for code-mode namespace
exclusion/direct-only, `sleep_tool=false`, shell/apps/plugins/multi-agent off,
bundled skills and memories off, `agents.enabled=false`, request-input off,
view-image off, web search disabled, and browser/computer/image/app feature
disables. Its full raw render is
[`prompt-input-candidate-04.json`](preparation/evidence/prompt-input-candidate-04.json),
SHA-256
`130774f4840003de874b61f00df3b6b54fbc09aa816a493088f0f32fb4be1ecc`.
`request_user_input`, `request_user_input_async`, and `clock.sleep` are absent
from that render, showing the corresponding visible controls applied there.
However, the declaration still includes `functions.exec` and `functions.wait`,
plus nested `list_mcp_resources`, `list_mcp_resource_templates`,
`read_mcp_resource`, and `apply_patch`. The generic `exec` description also
advertises access to the nested `tools` object. The prompt includes the exact
task instruction, developer permission instructions, and user environment
context. No assistant prior-turn message, project `AGENTS.md`, or skill or
memory content is present in this particular static render. That observation
does not prove the authenticated runtime input is identical.

The thread/start and turn/start field excerpts are now retained locally in
[`app-server-thread-turn-schema-excerpts.txt`](preparation/evidence/app-server-thread-turn-schema-excerpts.txt)
with hashes for the full generated schema source files, so the quoted field
semantics do not depend on a temporary directory.

**Step 1 disposition:** the maintainer accepts the remaining declarations and
injected context as a known issue and keeps the CLI route. Further removal of
the outer wrapper is no longer a prerequisite to preparation. The static
observations and authenticated-boundary uncertainty remain as recorded; no live
call or additional capability is established by this disposition.

## Baseline accounting disposition

Final reports will show raw usage categories, adjusted input, and adjusted
complete tokens. Subtract the applicable measured fixed input baseline once per
session, including each of B's three and C's 24 calls per repetition, while
retaining complete provider-total output consumption without double-counting
reasoning tokens. The
[protocol](protocol.md#candidate-invocation-and-input-overhead) owns baseline
provenance, the pre-trial freeze, drift/recalibration, unknown and negative
values, complete output accounting, aggregation, and raw-consumption budget/cost
rules.

No matched configuration baseline is frozen here. The 7,983 input tokens from
attempt 04 include its neutral task and all other supplied input; they do not
measure exact unintended-context tokens. The separate 7,380-token observation
remains maintainer-reported. Neither value is universally subtractable across
efforts or configurations. The neutral prompt contribution belongs in a measured
baseline unless separately measured and removed by the declared calculation.
Opaque dynamic metadata and unavailable runtime binding/context remain limits
to declaring an applicable fixed baseline. Missing baselines or usage leave
adjusted totals unavailable, rather than inferred from these greetings.

Attempt counts remain none 4/4 and total 4/16; the other efforts remain
not-started. This disposition neither replenishes the exhausted none allowance
nor performs other-effort calibration. Raw evidence files remain unchanged.

[candidate-record]: preparation/evidence/prompt-input-candidates.json

## Bounded process cleanup preparation

The maintained process owner is `script/process_supervisor.py`. Its native
async `run_bounded` API owns one command in a dedicated POSIX session, retains
the leader's actual return code, caps combined stdout and stderr, and applies
the execution deadline until leader exit and both pipe EOFs have been
observed. The public boundary enforces the protocol's 300-second execution,
10-second cleanup, and 1 MiB combined-output caps; stdin is closed unless an
input contract is added. Callers can compose invocations with a `TaskGroup`, a
bounded semaphore, and a shared cancellation event. Task cancellation is
re-raised only after shielded cleanup; the synchronous CLI adapter owns SIGINT
and SIGTERM once, converts them to shared cancellation, and restores prior
handlers. Cleanup signals only the verified session group, escalates from TERM
to KILL within the cleanup budget, reaps the leader, closes its pipes, and
reports an unresolved group as incomplete. A process-group probe observes
group presence but does not distinguish live members from descendant zombies.
Descendants that deliberately leave the owned session are outside this bounded
ownership guarantee. Permission errors remain explicit cleanup failures. OS
process creation itself cannot be forcibly interrupted; cancellation during
creation waits for the acquisition task to settle so any acquired handle can
be cleaned before cancellation is re-raised.

`test/script/integration/test_process_supervisor.py` exercises normal and
nonzero leader exits, a leader that exits while a descendant holds its pipes,
a descendant that closes inherited pipes, a leader that closes its own pipes
while continuing to run, a TERM-resistant descendant, combined output
overflow, exact-cap output, closed stdin, real SIGINT and SIGTERM cancellation,
invalid limits, permission denial, unverified group identity, and injected
output-callback exceptions. Concurrent invocations verify isolated output,
caller-limited process starts, and shared cancellation. Controlled tests cancel
during acquisition and repeat cancellation during cleanup. Tests use readiness
handshakes and disposable processes with bounded waits and independent finalizer
cleanup; they also prove that one task's cancellation leaves its active sibling
running successfully and that TaskGroup cancellation settles every owned child.
The optional `codex --version` check through the same process owner
reports the installed version and exercises CLI startup and leader
status/reaping only, with no model request. It does not prove descendant
behavior inside Codex or authenticated/model execution.

The historical attempt 04 cleanup `PermissionError` remains unexplained. The
retained record does not include a traceback or enough process-state detail to
identify why that signal was denied. The implementation fixes the demonstrated
unconditional-signal and lost-leader-status defects without attributing that
historical error to a specific host restriction. All Evaluation acceptance
criteria remain TODO, and the accepted CLI-context and matched-baseline
accounting dispositions above are unchanged.
