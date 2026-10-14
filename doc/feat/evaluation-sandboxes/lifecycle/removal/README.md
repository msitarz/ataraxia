# Preservation-aware sandbox removal

Removal implementation depends on the completed and merged
[disposability-proof Investigation](../disposability-proof/README.md). Before
implementation, update this contract under review to name the accepted proof
and owner for commits and private output; the Investigation must not be
bypassed by assuming a design here.

Removal also depends on the completed and merged
[active-state exclusion contract](../active-state-exclusion/README.md). Acquire
its per-sandbox claim before final removal checks and hold it through deletion;
execution uses the same claim protocol. This Work consumes that contract and
does not redefine locking or crash recovery. Capture the generation ID before
waiting for the claim; after acquisition, abort if the name or destination now
identifies another generation.

After [managed sandbox creation](../../../../evaluation-sandboxes.md), deliver
`make sandbox-remove NAME=...` using the shared
[root and ownership resolution](../../README.md#shared-root-and-ownership).
Removal is limited to the named direct child and its owned private artifacts.

The [disposability-proof Investigation](../disposability-proof/README.md) owns
the decision about evidence that permits disposal of meaningful commits and
private output. Until its result is accepted and this contract updated, missing
or inconsistent delivery proof must preserve the child and its artifacts. A
clean Git status alone is not delivery. Do not add a force option or registry.

## Acceptance

- **AC-1 TODO** Removal deletes only a named, direct, owned child under the
  shared managed root. It refuses the source/root, unowned or conflicting-owner
  child, symlinked or escaped paths, malformed ownership, and a child whose
  active-state claim cannot be acquired. Failed preparation is removable only
  when the child contains no meaningful work or undelivered output. After
  successful deletion, remove the generation metadata last, but retain the
  stable per-name lock object so a later create can use the name with a fresh
  ID. If cleanup fails or is interrupted, preserve the generation record and
  fail closed on name reuse.

  Validation: criterion-marked Make-boundary tests cover successful removal
  and each refusal class, including symlink/dangling-symlink, escaped-path,
  and held-claim cases. Reuse the active-state Work's concurrency evidence;
  independently review its claim is acquired before final checks and held
  through deletion. Verify the generation record is removed only after owned
  child/private data is gone, the per-name lock object remains intact, and a
  subsequent create uses a new generation ID; confirm owner/root agreement
  with creation.
- **AC-2 TODO** Removal refuses dirty tracked, staged, or untracked workspace
  content; meaningful commits beyond the recorded preparation base without
  delivery proof selected by the completed Investigation; and private output
  without the accepted retention/disposition proof. No refusal deletes or
  rewrites workspace, private artifacts, or failure diagnostics. Successful
  removal is allowed after work/output is proven disposable and the child is
  inactive.

  Validation: criterion-marked fixtures exercise dirty/staged/untracked files,
  a meaningful commit without delivery proof, accepted delivery proof, and
  retained private output without disposition. Assert rejected workspace and
  private trees are byte-for-byte unchanged; independently inspect proof
  against the owner named by the completed Investigation rather than treating
  clean status as proof.
