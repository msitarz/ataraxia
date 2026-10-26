# Supplied Codex quota capture

## Provenance and scope

The maintainer supplied this transcript on 26 October 2026. The original capture
files were not independently inspected or verified. This record retains one
exhausted five-hour quota case and a separate interactive status observation; it
does not establish the
[quota-wait criterion](README.md#ac-6-todo-optional-quota-waiting-preserves-the-active-run).

## Exec observation

The supplied probe used `codex exec --json`, Codex CLI version
`codex-cli 0.164.0`, model `gpt-6-luna`, reasoning effort `none`, minimal
instructions, disabled tools, and an empty working directory with read-only
access.

- Start: `2026-10-26T12:07:19Z`.
- End: `2026-10-26T12:07:23Z`.
- Exit status: `1`.
- Stderr: empty.
- Stdout: the following supplied JSONL, retained verbatim.

```jsonl
{"type":"thread.started","thread_id":"01a1781b-a54f-7763-9f82-74709e5e0fcf"}
{"type":"turn.started"}
{"type":"error","message":"You’ve hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage to purchase more credits or try again at 1:18 PM."}
{"type":"turn.failed","error":{"message":"You’ve hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/settings/usage to purchase more credits or try again at 1:18 PM."}}
```

## Separate interactive status observation

The supplied interactive `/status` observation reported version `0.164.0`,
`Local background server`, OpenAI, a Plus account with account identity
redacted, and model GPT 6.1 Sol with medium reasoning. This model differs from
the exec probe's model.

- Five-hour window: `0% left`, resets `13:18`.
- Weekly window: `84% left`, resets `08:18 on 2 Nov`.

These are the supplied displayed values; this record does not convert them to
UTC or infer a reset date or timezone for the exec error's `1:18 PM`.

## Limits and remaining prerequisite

No structured quota code, reset, or window fields appear in this exec capture.
Its error message supplies a time without a date or timezone. This observation
does not establish that all events or CLI versions lack machine-readable quota
telemetry, and it does not by itself prove that no semantic result was produced.
Weekly exhaustion was not tested.

The detection and reset-information source interface remains unresolved. A
subsequent design investigation can examine a machine-readable status or reset
source, including how it covers both exhausted windows and unknown data. The
capture does not authorize parsing reviewer answers, substituting an app-server
schema for the exec schema, typed implementation, or further empirical calls.

## Supplied session telemetry excerpt

The maintainer later supplied the following excerpt and source coordinates. The
session file was not read or independently verified. The supplied path was
`~/.codex/sessions/2026/10/26/rollout-2026-10-26T15-16-14-01a17891-a93e-7071-ad37-21b587fd4bf3.jsonl`.
The envelope timestamp was `2026-10-26T14:16:19.536Z`, ordinal `16`, with
`type=event_msg` and `payload.type=token_count`.

This is only the supplied `payload.rate_limits` object, not a verbatim full row;
token-usage fields and other envelope or payload content are omitted.

```json
{"limit_id":"codex","limit_name":null,"primary":{"used_percent":35.0,"window_minutes":300,"resets_at":1793035268},"secondary":{"used_percent":21.0,"window_minutes":10080,"resets_at":1793603901},"credits":{"has_credits":false,"unlimited":false,"balance":"0"},"individual_limit":null,"spend_control_reached":null,"plan_type":"plus","rate_limit_reached_type":null}
```

The maintainer reports that sessions, including `exec --json` invocations,
create such files and that the `thread.started` ID correlates with session
lookup; the supplied filename contains
`01a17891-a93e-7071-ad37-21b587fd4bf3`. This is a reported correlation, not a
verified universal file-discovery rule or schema guarantee across CLI versions.

This sample identifies a candidate machine-readable format, but account and
allowance scope association, file correlation, freshness, and error handling
still require review. It is a timestamped snapshot rather than a live query;
rereading it cannot refresh its observation age. Other local sessions may
supply newer observations of external usage, while remote usage or early resets
may remain invisible without a new event. This non-exhausted sample does not
establish weekly-exhaustion behavior or permission to retry a blocked call.

## Authorized future polling condition

The maintainer subsequently chose a dedicated asynchronous quota poller using
`codex exec --json`, separate from evaluation attempts. The specified condition
is `gpt-6-luna` with effort `none`, minimal nonempty instructions and prompt,
plugins, tools, and MCP disabled, and a read-only empty working directory.
This records the requested future condition, not an observed probe, a verified
pricing comparison, or a validated CLI flag recipe. No additional calls were
made for this record.

The poller must positively confirm fresh availability for the evaluation's quota
scope before restarting eligible evaluation attempts; Luna availability does not
establish capacity for another model. Numeric session reset hints support
scheduling, while rereading old telemetry cannot establish availability. The
[quota-monitoring contract](README.md#ac-6-todo-optional-quota-waiting-preserves-the-active-run)
owns polling, budgets, cleanup, evidence, and failure requirements.
