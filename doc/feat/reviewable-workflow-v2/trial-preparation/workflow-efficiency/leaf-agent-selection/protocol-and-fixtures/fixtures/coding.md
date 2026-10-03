# Code fixture draft

**Status:** provisional. The historical change, baseline revision, source/test
paths, preservation inventory, and setup compatibility are not verified. This
is a task proposal, not a runnable handoff.

## Executor-facing draft

**Proposed task:** replay the bounded `BarProvider` CSV error-handling change.
On malformed CSV, raise a contextual `ProviderError` and preserve the original
parse failure as the exception cause. Keep existing behavior for valid input,
blank input, normal exhaustion, and provider cleanup on success and failure.
Add meaningful regression tests for the new failure and the preserved behavior.
Limit changes to the frozen provider and test paths. Return the patch and
check results. Do not commit, push, or create a PR.

**Prompt to finalize:**

> At the frozen base revision `[commit]`, update `BarProvider` at `[source
> path]` so malformed CSV raises a `ProviderError` with the context confirmed
> in the fixture. Preserve the original parse exception as its cause. Preserve
> behavior for valid and blank CSV, normal exhaustion, and resource cleanup on
> success and failure. Add focused tests at `[test path(s)]` for malformed
> input and each preserved behavior. Change no unrelated files. Run the frozen
> code checks and return the patch with their results. Do not commit, push, or
> create a PR.

Resolve the bracketed values and verify the error context before dispatch. Use
the exact prompt for all nine runs of this fixture.

**Expected outcome:** malformed input raises the required contextual domain
error with its cause intact; valid and blank input retain their behavior;
normal exhaustion and cleanup remain correct; focused tests cover these cases
and pass.

**Proposed checks:** `make test ARGS='[frozen focused test paths]'`,
`make lint-check ARGS='[frozen source and test paths]'`, and
`make format-check ARGS='[frozen source and test paths]'`. Add `make typecheck`
if the verified change affects annotations or error contracts. Freeze exact
commands before trial dispatch.

## Owning-parent-only material — exclude from leaf handoffs

- **Base revision:** TBD. Verify the revision immediately before the historical
  change and confirm it can be prepared with the current locked environment.
- **Historical reference:** TBD. Locate and verify the historical
  `BarProvider` change and record its immutable commit permalink. Do not copy
  its patch or solution into the executor prompt.
- **Paths and failure context:** TBD. Verify the `BarProvider` module, focused
  tests, and the exact useful context expected in `ProviderError` from the
  reference evidence before filling the prompt.
- **Preservation inventory:** verify from the selected baseline and tests that
  valid records, blank input, normal exhaustion, exception chaining, and
  provider/file cleanup on success and failure are the behaviors to preserve.
  Record exact expected outputs and cleanup evidence here, outside the
  executor-facing handoff.
- **Checks and setup:** confirm the focused test selection and applicable Make
  checks, tool versions, and locked environment work unchanged for every
  isolated run.

Until these items are verified, this fixture is not frozen and cannot be used
for a trial.
