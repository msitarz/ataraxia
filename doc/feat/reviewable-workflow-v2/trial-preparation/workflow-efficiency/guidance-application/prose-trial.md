# Prose trial

## Protocol

This first bounded experiment compared Luna at medium and low effort on the
same documentation task: edit `doc/orchestrator.md` only against the
[baseline revision from #107](https://github.com/msitarz/ataraxia/commit/c48b3663e32c59862ef7cfc5b761fc6a9fcdbd8e).
Executors used isolated detached worktrees, fresh `fork_turns=none` sessions,
the same prompt except for the worktree path, the same prepared environment and
baseline guidance, and local-only delivery without commits, push, or PR. The
parent knew the effort mapping and reviewed both initial artifacts before
corrections; review was unblinded.

Before execution, success meant preserving meaning and gates, adding no
obligations, and editing no outside file. Prefer fewer required review
findings; word reduction alone was not success. This tests effort on one task,
not fresh versus long-running sessions or the three planned interventions.

## Results

| Condition | Words/lines, initial → final | Corrections | Agent-recorded executor time (UTC) |
| --- | --- | --- | --- |
| Baseline #107 | 851 / 98 | — | Not measured |
| A, Luna medium | 643 / 74 → 681 / 78 (20.0% below baseline) | 1 | Initial 20:39:38–20:40:04 (26s); correction 20:43:35–20:43:49 (14s) |
| B, Luna low | 776 / 88 → 755 / 87 (11.3% below baseline) | 2 | Initial missing; corrections 20:43:42–20:44:03 (21s) and 20:45:11–20:45:28 (17s) |

Times are agent-recorded/reported on 2026-10-01 UTC and include edit and check
work, not pure inference latency. Parent review of both initial artifacts took
78 seconds (20:41:30–20:42:48); review of their first corrections took 33
seconds (20:44:26–20:44:59). Review of B's second correction began at 20:45:53;
its end was not recorded, so there is no total review-time comparison.

Initial artifacts and each correction passed `make doc-format` and
`make doc-check` over 53 Markdown files; `git diff --check` also passed. The
parent reused Luna's local check evidence. These local artifacts did not
receive CI.

## Review findings

- A's initial version weakened the current-revision cue, omitted the CI/review/
  merge gate-preservation statement, made the wait for a completed correction
  or blocker implicit, and removed an informational token-caching qualification.
  One correction restored the needed guidance.
- B's initial version repeated consolidated-correction and approval/scope
  reminders, and omitted requested UTC timestamps. Its first correction removed
  the stop condition for an unresolved finding after correction; a second pass
  restored it. Correction-pass times were recorded, while initial timestamps
  remained unavailable.
- Neither initial artifact was accepted unchanged. Both final artifacts were
  reviewed for meaning and passed the listed local checks. #107's baseline was
  unchanged.

## Recommendation and limits

Medium effort consolidated more and needed one correction; low effort needed
two. No reliable elapsed-time or cost winner can be selected: B's initial
duration is missing, exact dispatch times and token/cost data are unavailable,
and final B review timing is incomplete. This single pair also shared
an environment/cache and had different correction scopes. It cannot establish
a general effort effect.
Make no global effort-default change from this evidence; continue the broader
Investigation. Raw patch snapshots remain available locally if inspection is
needed; they are not copied into the Work or PR.
