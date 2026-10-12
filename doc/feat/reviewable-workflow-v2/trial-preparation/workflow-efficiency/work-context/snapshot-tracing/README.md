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

Keep the comparison and recommendation in this README, reviewable in about
five minutes. No implementation, permanent tooling, new tests, journal,
automatic stamping of every test, or policy adoption is in scope. A benchmark
or audit suite is not required. A no-change or inconclusive recommendation is
a valid result; any later implementation or adoption needs its own review.

## Acceptance

- **AC-1 TODO** Starting from a retained test's Work path and AC ID after
  contract cleanup, the comparison shows how existing Git navigation finds
  the historical contract and how an optional verification SHA would change
  that lookup, identifying observed convenience and limits.
  Validation: independently inspect the source references and concise manual
  examples, with commands and observed outcomes distinguished from proposed
  behavior; confirm neither candidate assumes historical test selection.
- **AC-2 TODO** For both candidates, the comparison explains available and
  absent refs, paths, and ACs; Git reachability; the verification/cleanup pair;
  rebase maintenance and circular-reference risk; and the optional reference's
  compatibility needs and limited historical-contract meaning.
  Validation: independently review those cases against inspected current
  machinery and the delivery owner, distinguishing checked facts, hypothetical
  behavior, and unresolved feasibility.
- **AC-3 TODO** The recommendation weighs lookup convenience against
  maintenance cost and gives a supported change, no-change, or inconclusive
  outcome without implementation or adoption.
  Validation: independently compare the recommendation with AC-1 and AC-2
  evidence and uncertainty; confirm it preserves guidance owners and does not
  treat a SHA as test introduction, `DONE` proof, or current test success.
