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

The C/D extension used the same #107 baseline and original prompt except for
the worktree path, without added feedback hints. It used the same local-only,
isolated fresh-session setup and prepared environment. C was GPT-6 Luna high;
D was GPT-6.1 Sol low. The parent knew prior findings and labels.

Before execution, success meant preserving meaning and gates, adding no
obligations, and editing no outside file. Prefer fewer required review
findings; word reduction alone was not success. These four runs sample
model/effort conditions on one task, not session age or the three planned
interventions.

## Results

| Condition | Words/lines, initial → final | Corrections | Agent-recorded executor time (UTC) |
| --- | --- | --- | --- |
| Baseline #107 | 851 / 98 | — | Not measured |
| A, Luna medium | 643 / 74 → 681 / 78 (20.0% below baseline) | 1 | Initial 20:39:38–20:40:04 (26s); correction 20:43:35–20:43:49 (14s) |
| B, Luna low | 776 / 88 → 755 / 87 (11.3% below baseline) | 2 | Initial missing; corrections 20:43:42–20:44:03 (21s) and 20:45:11–20:45:28 (17s) |
| C, GPT-6 Luna high | 821 / 95 → 804 / 94 (5.5% below baseline) | 1 editorial | Initial 21:04:06–21:05:48 (102s); correction 21:07:35–21:08:21 (46s) |
| D, GPT-6.1 Sol low | 752 / 88 → 752 / 88 (11.6% below baseline) | 0 | Initial 21:04:21–21:05:24 (63s) |

Times are agent-recorded/reported on 2026-10-01 UTC and include edit and check
work, not pure inference latency. Parent review of both A/B initial artifacts
took 78 seconds (20:41:30–20:42:48); review of their first corrections took 33
seconds (20:44:26–20:44:59). Review of B's second correction began at 20:45:53;
its end was not recorded, so there is no total review-time comparison.

Parent dispatch windows for C/D were coarsely observed: C between
21:03:28 and 21:04:03, D between 21:04:03 and 21:04:22; both initial returns
were observed by 21:06:11. Initial review took 63 seconds (21:06:11–21:07:14).
C correction dispatch was observed between 21:07:24 and 21:07:36; the result
arrived by 21:08:38 and its review took 51 seconds (through 21:09:29). These
windows are not exact executor durations.

A/B initial and correction artifacts passed `make doc-format` and full
`make doc-check` over 53 Markdown files; `git diff --check` also passed. C
passed scoped doc-format/doc-check and diff checks. D passed scoped
doc-format and full doc-check; the parent supplied its missing diff check. The
parent reused Luna's local check evidence. None of these local artifacts
received CI.

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
- In the A/B pair, neither initial artifact was accepted unchanged. Both
  final artifacts were reviewed for meaning and passed the listed local
  checks. #107's baseline was unchanged.
- C initially preserved meaning but retained duplicate correction and
  approval/scope reminders; one editorial correction consolidated them. Its
  final preservation review passed.
- D's first draft passed the preservation and duplication review without
  correction. It centralized approval, scope expansion, and correction-stop
  rules while preserving recovery and gates.

## Recommendation and limits

Among these four first drafts, only D was accepted unchanged; Luna high retained
duplication that Luna medium had consolidated. More effort did not
monotonically improve concision or correction count. No complete time or cost
ranking is supported: B's initial duration and token/cost data are missing,
final B review timing is incomplete, C/D batches differ from A/B, and effort
labels across models are not equivalent compute budgets. The shared cache,
concurrency, one sample/configuration, and different correction scopes further
limit comparison. Keep the global default unchanged and run more matched
trials. The broader fresh-versus-long and intervention Investigation remains
incomplete. Raw patch snapshots remain available locally if inspection is
needed; they are not copied into the Work or PR.
