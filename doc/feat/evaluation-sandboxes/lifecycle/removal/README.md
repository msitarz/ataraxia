# Preservation-aware sandbox removal

After
[active-state delivery](../../../../evaluation-sandboxes.md#delivered-lifecycle-safety),
deliver `make sandbox-remove NAME=... [SANDBOX_ROOT=/absolute/path]` using
shared
[root and ownership resolution](../../README.md#shared-root-and-ownership).
Acquire the stable exclusive OS lock before final checks and hold it through
deletion. Revalidate captured generation and destination identity before acting.
The shared lifecycle protocol defines marker, disposition and recovery; this
Work consumes them without another proof record or Investigation.

Delete only the named direct child and its explicitly owned private artifacts.
Require a current disposition recorded by its owning orchestrator after artifact
preservation and maintainer review, bound to the current workspace, run and
output. Verify retained destinations/evidence before destructive action; reject
missing or inconsistent preservation. Meaningful commits, dirty/staged/untracked
content and private output must all be covered by preserved exact artifacts or
explicit reviewed discard decisions. Clean Git status and inactivity alone are
insufficient. No force option bypasses these guards.

Failed preparation requires the same disposition, including partial workspace
and failure diagnostics; a missing partial directory does not authorize deleting
its remaining marker/output. Unknown execution or potentially live descendants
refuse cleanup. Refusal preserves workspace, private output and diagnostics.
After successful deletion remove the generation marker last and keep the stable
lock file. Partial failure/interruption retains the marker and remaining
material, records incomplete cleanup when safe, and blocks name reuse; retry
revalidates identity, disposition and retained evidence under the lock. Never
follow symlinks or recursively traverse another owned sandbox/private tree by
artifact path.

## Acceptance

- **AC-1 TODO** Only a named, direct, owned child with supported metadata,
  verified inactive execution and current reviewed disposition can be removed
  under exclusion. Unsafe root/source, foreign ownership, symlinks, escapes,
  malformed metadata, stale generation, busy lock and unknown descendants
  refuse.

  Validation: criterion-marked Make-boundary fixtures cover success and every
  refusal, plus a launch racing final checks/deletion. Independently review
  claim lifetime and exact root/owner agreement; reuse shared concurrency
  evidence.
- **AC-2 TODO** Exact workspace work, commits, private artifacts and failed
  preparation diagnostics are preserved or covered by an explicit reviewed
  discard decision before removal. Changed or absent bindings invalidate
  approval and all refusals leave protected data unchanged.

  Validation: criterion-marked fixtures cover dirty/staged/untracked content,
  meaningful commits, private output, failed preparation, missing retention,
  valid disposition, wrong owner and changed run/output/workspace after
  approval. Assert refusal preserves bytes; independently inspect
  review/preservation evidence without treating clean status as delivery.
- **AC-3 TODO** Successful cleanup removes the marker last, retains stable lock
  identity and permits a new generation. Failed/interrupted cleanup preserves
  remaining evidence and blocks unsafe reuse; safely validated retry can finish.

  Validation: criterion-marked staged-failure fixtures interrupt child/private
  deletion and marker removal, inspect remaining material and refusal of create,
  then exercise guarded retry and same-name recreation. Verify retained
  artifacts outside the cleanup set remain intact.
