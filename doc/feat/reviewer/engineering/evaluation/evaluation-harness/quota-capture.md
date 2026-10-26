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
