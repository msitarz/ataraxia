# Acceptance snapshot tracing

Would an optional verification-commit SHA on a retained test make its reviewed
historical Work contract easier to find than the existing Work path, AC ID, and
Git history, enough to justify maintaining that reference? Compare no change
with adding the reference during the later cleanup commit. This is an
[Investigation](../../../../../../work-definition.md#investigations), not
authorization to implement or adopt a marker or policy. It is independent of
completion routing and the context tool. Existing reading routes and guidance
owners remain authoritative: [handoffs](../../../../../../orchestrator.md),
[PRs](../../../../../../pull-requests.md), and
[acceptance tracing](../../../../../../acceptance-tracing.md).

## Starting point and bounds

At verified base `06edc55875ad72b7baf995cf1b47bf10afe04506`,
`script/work_paths.py` requires an existing owning file for Work-targeted
commands. `script/acceptance_tests.py` selects current tests by `work` and `ac`;
`script/acceptance_coverage.py` rejects extra keywords on selected `covers`
markers. The
[delivery procedure](../../../../../../acceptance-tracing.md#work-delivery-commits)
retains the reviewed contract in a verification commit before separate cleanup,
preserves that pair through linear integration, and requires reference refresh
when rebasing changes referenced commits. Git retains removed contracts.

The proposed reference would identify the reviewed historical contract at that
verification commit, scoped by the existing Work path and AC ID. It would not
identify when a test was introduced, establish `DONE`, or prove current test
success. Its representation, including any marker keyword name, is provisional.
Inspect the smallest compatibility changes it would need; do not assume the
current checker accepts extra metadata or that historical test-selection tooling
is necessary.

Use source inspection and a few concise manual examples with current Git and
acceptance machinery. Compare finding the contract from a surviving test's
Work path and AC ID with finding it from an optional SHA. Check available and
absent references, a missing path or AC at a referenced revision, and whether
ordinary Git navigation and reachability suffice. Examine the retained
verification/cleanup pair, rebase hash maintenance, and circular references if
inserting or refreshing a SHA changes the very commit it names. Distinguish a
resolvable commit from evidence of review. Describe any limits rather than
building recovery or enforcement tooling.

## Findings and recommendation

**Observed at `2225e4d`:** `script/work_paths.py::resolve_work_file` accepts
only a normalized repository-relative `README.md` or `spec.md` that currently
exists. `script/acceptance_tests.py::build_command` selects with `work` and
optional `ac`; it does not load historical contracts. In
`script/acceptance_coverage.py::_selected_marker_criterion`, a marker selected
for the Work being checked must contain exactly the supported literal `work`
and `ac` keywords. A third SHA keyword currently makes `ac-check` report that
the selected marker needs literal Work and AC strings. The checker reports
declarations; it does not validate historical test selection or certify a
criterion.

One existing, removed Work makes the lookup concrete. Current
`test/make/integration/test_worktree_pruning.py` has surviving markers for
`doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md`,
including AC-2. Commit `4b3e886156d4c223f2fff9b4c961920bb3dfb1f6`
(`feat: add safe linked worktree cleanup`) is the retained
implementation/evidence commit; it contains the contract with AC-2 DONE. Its
next commit, `af33a9303cd795a674359e70cedb4002a5a3737b`
(`docs: complete worktree cleanup Work`), removes that README and updates the
parent map. Both commits are ancestors of this checkout.

Manual Git examples, run in this checkout:

```text
git show 4b3e886:doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md | rg -n 'AC-2 DONE'
  -> matched the retained AC-2 DONE line (line 51)
git show af33a93:doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md
  -> fatal: the named README does not exist in af33a93
git show 4b3e886:doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md | rg -n 'AC-99'
  -> no match (exit 1)
git cat-file -e 4b3e886^{commit}
  -> exit 0; the commit object resolves
git cat-file -e ffffffffffffffffffffffffffffffffffffffff^{commit}
  -> exit 128; fatal: Not a valid object name
git merge-base --is-ancestor 4b3e886 HEAD
  -> exit 0; the verification commit is reachable from this checkout
git log --oneline -S'AC-2 DONE' -- doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/worktree-cleanup/README.md
  -> listed cleanup commit af33a93 then evidence commit 4b3e886
```

The abbreviated revisions above identify the full hashes stated in the text.
These examples show that ordinary `git show <verification-sha>:<path>` locates
the contract and requested AC directly, while `git log -- <path>` or
`git log -S'AC-2 DONE' -- <path>` can find the relevant history when the SHA is
unknown. A SHA on the surviving test would make the first lookup direct, but
would not change what the acceptance tools select. An absent or misspelled SHA
fails to resolve; a resolving SHA can still name a commit without the requested
path or AC, as the missing-path and AC-99 examples show. A resolvable object
alone is not proof that its contract was independently reviewed. Reachability
from maintained history keeps the object available; a marker does not pin an
otherwise unreachable object against eventual Git garbage collection.

The retained verification commit followed by a cleanup commit already gives a
stable navigation point in ordinary history. A rebase can replace the
verification commit ID, so a stored SHA would need refresh in the later cleanup
commit. That refresh changes the cleanup commit ID too, but not the earlier
verification commit it names. Inserting the SHA into the verification commit
itself would be circular because changing that commit's contents changes its
ID. Keeping the reference exclusively in the subsequent cleanup commit avoids
that cycle. The current `ac-check` compatibility issue still means a marker
field needs a small checker contract change and focused validation before it
could be adopted.

**Recommendation: no change.** Git already exposes the retained contract by
path and AC, and this repository's retained pair keeps that commit reachable.
The optional SHA saves a short history lookup in an occasional manual recovery
case, while adding per-test metadata, checker compatibility work, and a
rebase-refresh obligation. The inspected example establishes that navigation
works; it does not measure human lookup time or show that people need the
shortcut often enough to offset its maintenance. Do not treat the reference as
test-introduction history, `DONE` evidence, or proof of current test success.
If a later observed case shows ordinary history is inadequate, review that
need and a compatible representation separately.

Keep the comparison and recommendation in this README, reviewable in about
five minutes. No implementation, permanent tooling, new tests, journal,
automatic stamping of every test, or policy adoption is in scope. A benchmark
or audit suite is not required. A no-change or inconclusive recommendation is
a valid result; any later implementation or adoption needs its own review.

## Acceptance

- **AC-1 DONE** Starting from a retained test's Work path and AC ID after
  contract cleanup, the comparison shows how existing Git navigation finds
  the historical contract and how an optional verification SHA would change
  that lookup, identifying observed convenience and limits.
  Validation: independently inspect the source references and concise manual
  examples, with commands and observed outcomes distinguished from proposed
  behavior; confirm neither candidate assumes historical test selection.
- **AC-2 DONE** For both candidates, the comparison explains available and
  absent refs, paths, and ACs; Git reachability; the verification/cleanup pair;
  rebase maintenance and circular-reference risk; and the optional reference's
  compatibility needs and limited historical-contract meaning.
  Validation: independently review those cases against inspected current
  machinery and the delivery owner, distinguishing checked facts, hypothetical
  behavior, and unresolved feasibility.
- **AC-3 DONE** The recommendation weighs lookup convenience against
  maintenance cost and gives a supported change, no-change, or inconclusive
  outcome without implementation or adoption.
  Validation: independently compare the recommendation with AC-1 and AC-2
  evidence and uncertainty; confirm it preserves guidance owners and does not
  treat a SHA as test introduction, `DONE` proof, or current test success.
