# Independent shallow clone readiness

Depend on the [dependency snapshot](../dependency-snapshot/README.md). Own an
optional Make preparation entry point alongside the existing worktree target.
Use the [clone and setup recipe](../../sandbox-isolation/successful-recipe.md)
without duplicating its runtime settings catalog. Selected committed state is
input; source dirty files and inherited source hooks are not.

Keep this leaf within a five-minute review; split before oversized execution.
Automated tests use criterion markers scoped to this README; manual judgments
remain independent review. All criteria are planned, not observed evidence.

## Acceptance

- **AC-1 TODO** Given a fresh destination and frozen selected base, preparation
  creates an independent depth-one single-selected-branch clone at that exact
  HEAD, without tags, origin, alternates, hardlinked objects or dirty source
  inputs; changed base or existing destination is rejected. Local `master` is
  the default source branch/base under
  [CONTRIBUTING](../../../../../../../../CONTRIBUTING.md#work-branches-review-and-merge);
  any override requires a separate explicit selected branch/base instruction.
  Assign the requested executor branch without retaining extra source refs.

  Validation: Criterion-marked Git fixture tests inspect refs, shallow history,
  object independence, default/explicit base selection, assigned branch and
  rejection paths; regression tests preserve the regular
  worktree interface.
- **AC-2 TODO** The vetted snapshot prepares a fresh virtual environment through
  locked offline Make setup, installed hooks and readiness checks; missing cache
  or failed checks retain recoverable state without full-history or network
  fallback.

  Validation: Criterion-marked integration tests exercise actual Make
  setup/readiness and missing-cache failure with fresh destinations;
  independently review supported platform/tool/cache pins and diagnostics.
