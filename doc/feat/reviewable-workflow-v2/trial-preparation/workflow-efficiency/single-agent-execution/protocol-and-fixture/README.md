# Protocol and fixture

Define the comparison for the parent [Investigation](../README.md); do not run
trials or record results.

Freeze a separate, bounded documentation fixture: a supplied `facts.md` and
`guide.md`; rewrite only `guide.md` under the headings Preconditions, Steps,
and Limits, preserving every enumerated fact and link without adding rules.
Pin files, brief, base, guidance, tools, and rubric. No PR, merge, or live-CI
actions; this must not be this or another Investigation.

Compare three randomized pairs: one direct Luna-low executor against one
Luna-low orchestrator and its fresh Luna-low executor (nine sessions total).
Use isolated fresh sessions and workspaces; no nested delegation. The
orchestrator reviews its return; one independent evaluator scores all six
artifacts, blind to condition where practicable, recording any unblinding.
Measure role active minutes, setup/context reading, progress and steering
messages, checks/repeats, correction rounds and causes, artifact-ready time,
reviewer minutes separately, and role tokens/cost or `unknown`. Use local
validation only; PR-ready/live-CI time does not apply.

Per-run gates require all headings, facts, and links, no invented rules, changes
only to `guide.md`, and passing local Markdown checks. Every run in a winning
condition must pass. A direct-execution win requires at least two of three pairs
to reduce executor, orchestrator, and steering minutes versus control by both
15% and 10 minutes, with no more than one extra correction round or five extra
steering minutes in the direct run of either qualifying pair. Report paired
results, median, range, and limits. Missing pairs or any gate failure means no
winner; allow inconclusive/no-change.

Freeze the exact prompts. The direct executor and control executor get the
same request: “Execute the fixture Work at `<path>` from `<revision>`. Read the
Work and listed guidance, make only the contracted edits, run its local checks,
and return the artifact and criterion evidence. Do not delegate or take PR,
merge, or policy actions.” The control orchestrator gets that request plus:
“Own scope and review. Make exactly one handoff to a fresh Luna-low executor,
independently review its completed return, and report combined evidence; do not
implement the changes.”

Proposed authorization, to be completed with the frozen revision and prompts
after protocol review: “Authorize three randomized pairs (nine fresh Luna-low
sessions total) using fixture `<revision>`: each pair has one direct executor
and one Luna-low orchestrator making exactly one handoff to a fresh Luna-low
executor. Authorize only those three handoffs. No live PR, PR-ready state,
merge, or policy adoption is authorized. Preserve independent evaluation and
maintainer review. This local trial is not CI evidence; any resulting PR still
requires the full CI gate.” Missing revision or prompt means stop.

## Acceptance

- **AC-1 TODO** A standalone documentation fixture, bounded prompt, and
  acceptance rubric are frozen at a revision and do not depend on this
  Investigation's completion.
  Verification: inspect the fixture tree and execute the brief manually.
- **AC-2 TODO** The nine-session design, matched prompts and conditions,
  independent evaluation, measurements, per-run gates, denominator, and
  thresholds are explicit and locally reviewable.
  Verification: walk through one pair and calculate example passing,
  failing, and inconclusive outcomes.
- **AC-3 TODO** The protocol names the required authorization and preserves
  current delegation, review, maintainer, and CI boundaries.
  Verification: inspect the proposed dispatch text and confirm it cannot be
  read as authority to run trials.
