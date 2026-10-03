# Documentation fixture draft

**Status:** independently reviewed frozen fixture, pending integration and
explicit maintainer authorization. The source and task scope are identified;
no trial has run and no dispatch is authorized.

## Executor handoff

**Frozen file:** `doc/orchestrator.md` at the fixture input prepared by the
owning parent.

**Exact executor prompt:**

> In the prepared checkout, edit only `doc/orchestrator.md`. Consolidate the
> repeated Luna-low reasoning-effort
> statement between the paragraph beginning “For a Work tree” and the
> following paragraph beginning “Delegate repository changes”. Keep the
> direct parent-to-leaf assignment and owning-parent review; retain the
> general Luna-low default and the requirement for maintainer approval of
> higher effort. Preserve the remaining Work-tree roles and scheduling rules,
> Work sizing and split process, scope-growth stops, worktree steps, review and
> recovery guidance, evidence requirements, and human, merge, and CI gates.
> Change no other file. Run `make doc-format ARGS=doc/orchestrator.md`,
> `make doc-check ARGS=doc/orchestrator.md`, and `git diff --check`; return the
> patch and their results. Work from the checked-out tree only. Do not inspect
> commit history, refs, tags, historical patches, or parent-only fixture
> material. Do not commit, push, or create a PR.

Use this exact prompt for all nine runs of this fixture. The parent verifies
the frozen `doc/orchestrator.md` blob before handoff; stop if it does not
match.

**Expected outcome:** only the named subsection changes; redundant explanation
is reduced; the reviewer confirms all baseline requirements and links remain
intact; the declared checks pass.

**Checks:** `make doc-format ARGS=doc/orchestrator.md`,
`make doc-check ARGS=doc/orchestrator.md`, and `git diff --check`. These were
run against the fixture base; rerun them for every trial artifact.

## Owning-parent-only material — exclude from leaf handoffs

- **Frozen input:** runtime/guidance base
  [f7e03b6](https://github.com/msitarz/ataraxia/commit/f7e03b6237ac240b41e784d1e9cdd4dac1118ccd);
  [`doc/orchestrator.md` at that revision](https://github.com/msitarz/ataraxia/blob/f7e03b6237ac240b41e784d1e9cdd4dac1118ccd/doc/orchestrator.md)
  has blob `cd886039148f5c3af1d8adf6aeed42c2443a1909`. This differs from the
  earlier [prose trial baseline](../../../guidance-application/prose-trial.md),
  whose document blob is `653947c51429fde9d4c8cba165f1299af7f857cf`.
- **Verified redundancy:** the `For a Work tree` paragraph and following
  `Delegate repository changes` paragraph both set the Luna-low effort
  default. The Work-tree paragraph was added in
  [tree-orchestration commit 839a55b](https://github.com/msitarz/ataraxia/commit/839a55ba87e5688539fdd45ae90bbcead8b5da6e);
  that tree-specific instruction did not exist in the prose-trial baseline.
- **Preservation inventory:** preserve all distinct Work-tree ownership,
  direct leaf delegation, parent review, no-wrapper default, subtree
  integration, check reuse, dependency scheduling, and no-invented-layer
  rules. Preserve the general Luna-low default; higher-effort and alternate-
  agent approval; Work sizing, split-plan review and maintainer exception;
  stop/report/split behavior for out-of-scope work; worktree setup; correction
  and stall handling; interruption recovery; PR/evidence reporting; and human,
  merge, and CI gates. Only the repeated effort phrase is consolidation scope.
- **Fixture integrity:** before each trial worktree is handed off, verify that
  `doc/orchestrator.md` has this exact blob. Create from the frozen f7e03b6
  base even if local `master` has advanced; do not mix later guidance into a
  trial checkout. The executor prompt omits commit identifiers; the owning
  parent verifies the blob before handoff.
- **Setup:** use the guidance and locked tools from the trial base. The
  formatter and link check passed on the identified input.

This reviewed frozen fixture does not authorize dispatch. The controlled
comparison remains blocked on integration and explicit maintainer
authorization.
