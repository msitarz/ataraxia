# Reviewed fork import and Work-branch delivery preparation

The maintainer authorized this bounded deterministic candidate: after reviewer
acceptance and final executor correction, the orchestrator fetches approved fork
commits into a full-history repository, rebases onto its designated Work branch,
then follows normal maintainer PR review. The selected path passed after one
reviewed editor harness correction. Initial failure and preparation provenance
remain retained below. It changes no production Make target, live repository
branch or remote, and performs no model or credential action. All Work
acceptance remains TODO.

## Frozen integrated input and disposable destinations

Fresh artifact root: `/private/tmp/ataraxia-delivery-9f2b7c18db15`. Only the
reviewed runner may construct new destination repositories beneath it. The
actual accepted TMPPREFIX executor clone remains read-only input at
`/private/tmp/ataraxia-isolation-tmpprefix-2df60f7109cc/clone`. Its approved
branch is `refs/heads/master`, with initial commit
`efefa0ed26c20eb532c94990f0019f2b7c53a531` and resumed commit
`dcc22b3f7596dc01789c8eac59531b2b0e669672`, above base
`83bc8542fad85d7f49fc0205d578bf8c5e40bbbb`. This uses the
[reviewed standalone result](../sandbox-isolation/standalone-model.md#completed-standalone-b-actual-executor-and-resume).
No auth/session directory is copied or inspected.

The integrated receiver is a new full-history clone of the original disposable
source, single master/no tags/no local optimization/no depth. It creates
`work/delivery` at the frozen base, imports only the explicit approved branch
into `refs/remotes/executor/assigned`, without tags or other executor refs,
fast-forwards and rebases at the unchanged base. It must retain the approved
commit IDs/order, only-task diff and exact verified bytes. Receiver
`.git/shallow` must not exist. Master is never the delivery target.

The approved clone's 48 file/symlink entries are hash/target-frozen, including
refs, shallow marker, local config, hook/helpers and scratch. Before and after
imports/publication, the runner verifies the identical snapshot, absent remote
and alternates, final HEAD and excluded H0/side objects with actual Git
missing-object diagnostics. No receiver/publication configuration is written
into the executor clone. This establishes unchanged input conditions; it does
not reexecute sandbox denial after publication setup or claim additional access
boundaries.

## Separate delivery-boundary fixture

A newly constructed full-history fixture has older history, selected master
base and assigned Work commits. Its implementation includes changed text,
binary bytes `00ff0a0304`, rename, deletion and executable mode `100755`.
Fixture criteria/evidence and parent-map files simulate the
[delivery commit contract](../../../../../../acceptance-tracing.md#work-delivery-commits);
they are disposable data, not completion of real Work criteria.

Root independently reviews staged fixture criteria at a first checkpoint before
marking its fixture contract DONE, committing implementation/evidence and making
a distinct cleanup commit. Four receivers then cover:

- Integrated accepted executor commits at unchanged base, retaining identity.
- Independent fixture at unchanged base, retaining identity and two boundaries.
- Advanced Work base with unrelated upstream file: clean rebase retains that
  file, exact work tree changes, authors/author dates/subjects/order and
  separate implementation/evidence and cleanup commits, while IDs change.
- Conflicting upstream text: rebase must exit one with unmerged text and no
  publication. The orchestrator-owned runner applies the declared resolution
  `resolved-upstream+work` plus newline, continues noninteractively and repeats
  tree/metadata/boundary checks. Reconciliation belongs to the full-history
  receiver; the executor input is untouched.

All Git operations are separate subprocess calls with pinned Git, system/global
config disabled, fixture identity, signing disabled, no inherited hooks/editor
and no prompts. Git commands, statuses, stderr and output hashes are retained in
an exclusive private launch log. No process kill, reset, old-fixture cleanup,
network endpoint, authentication or alternate transport is included. Startup,
unexpected ref/head, source mutation, malformed conflict or verification failure
stops with evidence retained; no automatic repair/retry follows.

## Evidence refresh and local publication review

A second root checkpoint binds the plan hash and actual imported/rebased heads,
trees, metadata and conflict resolution. Root must inspect refreshed evidence
and accept commit boundaries before publication. The request/sentinel paths and
request SHA are printed; private sentinel JSON must bind that exact SHA.
Initial approval fields are `reviewed`, `evidence_refreshed` and
`fixture_criteria_reviewed`, all true. Final approval replaces the last field
with `publication_approved`, true. Both waits consume the shared budget.

Only after final acceptance does the runner initialize a disposable bare remote,
seed its master at the independent fixture base, and push explicit Work refs
`work/delivery/integrated`, `unchanged`, `advanced`, `conflict`. It verifies
four heads/trees/base ancestry, exactly those refs plus unchanged master, and no
shallow receiver. There is no live GitHub PR/push, real root mutation, CI run or
maintainer merge. The normal next path remains orchestrator-owned ready PR after
review, latest-head CI and maintainer review under
[PR publication](../../../../../../pull-requests.md).

## Exact execution boundary and limits

Pending root review and specific host execution from the existing worktree:

```text
python3 /private/tmp/ataraxia-delivery-9f2b7c18db15/evidence/delivery.py
```

Runner SHA256:
`123361cacbaf109fe6214ad214f91bb50c2c99474299c26ba44031044bf1f96f`.
Plan SHA256:
`2d351e439c2c8f33d810cee296af0afb6a358ee0af6549b0fb1387a91457b667`.
The immutable plan pins inputs, Git and environment; the reviewed runner freezes
command construction and fixture content. Runtime-derived commit IDs are
recorded before use, with expected Work HEAD checked before branch updates.
Each command has 30 seconds; the complete batch including both reviews shares
15 minutes. Syntax and newline-literal validation passed; no runner Git probes
have executed during preparation.

This tests the selected import/rebase path only. Format-patch/am, raw diff,
direct clone publication, missing-base/shallow receiver rejection, live
GitHub/credentials/CI, full project artifacts and post-publication sandbox or
model corrections remain unrun. Prior isolation and model observations stay
retained separately. No artifact-delivery AC is marked DONE by this preparation.

## Initial observed delivery and editor failure

Root approved and ran the original packet. Integrated import preserved both
accepted executor commit IDs in a nonshallow full-history receiver. Root then
reviewed staged fixture bytes/diff/criteria and approved the first checkpoint;
fixture implementation/evidence and separate cleanup commits were created.
Independent unchanged-base import and clean advanced-base rebase passed their
tree/metadata/order checks. Conflict rebase halted with the expected unmerged
text, and the declared reviewer resolution was staged.

Continuation failed at 09:21:49 UTC. Exact argv:

```text
/usr/local/Cellar/git/2.55.0/bin/git -c commit.gpgsign=false -c tag.gpgsign=false -c core.hooksPath=/dev/null -C /private/tmp/ataraxia-delivery-9f2b7c18db15/conflict -c core.editor=true rebase --continue
```

Exit one reported editor `/usr/bin/false`, requested a message with `-m` or
`-F`, and could not commit staged changes. The frozen environment supplied
`GIT_EDITOR=/usr/bin/false`, which overrides `core.editor=true`. This is a
noninteractive harness configuration error, not an import/rebase limitation. The
runner stopped, preserving staged conflict and rebase metadata. No publication
remote was initialized and nothing was published.

Raw log `evidence/launch-a82276367bc0482a82f7cacfcc4a31ce.jsonl`, original
runner/plan and first review request/approval remain unchanged. Conflict HEAD
is `0d3d10559af80d20dbb1c34a97b4de5886b79c2e`; its index, complete rebase
metadata and working bytes are frozen in the recovery plan. Successful fixture,
integrated, unchanged and advanced repositories are also hash-snapshotted.

## Single reviewed recovery condition

At preparation, orchestrator steering authorized one focused correction, pending
new specific host approval; the completed outcome is recorded below. The
recovery does not create a fresh matrix, repeat models or reset any fixture. It
verifies old plan/runner/log/checkpoint hashes, all frozen repository snapshots,
conflict HEAD/index/rebase state, prior successful outcomes and approved
executor invariants. It invokes the same continuation argv above with
`GIT_EDITOR=/usr/bin/true` only for that exact command; all other Git calls
retain the original false editor environment.

After continuation it repeats conflict tree/author/date/subject/order and
implementation/evidence-before-cleanup checks, uses a compare-and-swap Work-ref
update, and emits a new root review checkpoint. Root must accept refreshed
conflict evidence and publication before the previously declared local bare
pushes. Receiver head/tree/base/ref and unchanged-master checks then finish;
approved executor snapshot/remote/shallow/object invariants remain required.
Failure or repeated finding stops without another correction or publication.
Each command remains bounded at 30 seconds; the recovery including review has a
new 15-minute shared deadline.

Exact pending host command from the existing worktree:

```text
python3 /private/tmp/ataraxia-delivery-9f2b7c18db15/evidence/recover.py
```

Runner SHA256:
`7b67f720b549235bb434b2981cd21ac669898e09dc79c8c2466bec91ac86d749`.
Recovery-plan SHA256:
`09d2121b612c1d035c4434707f6393166dcfa632dc57ed5e471eb83d5c3f2f16`. Syntax and
newline-literal inspection passed. No recovery Git command or runner execution
occurred during preparation; no model/auth action, old state reset,
main-repository mutation or live publication is included. Acceptance remains
TODO pending completed observations and independent review.

## Completed reviewed import/rebase and local delivery

**Bounded selected path: PASSED.** Root approved the exact recovery runner,
which exited zero at 09:26:57 UTC. Its sole correction was
`GIT_EDITOR=/usr/bin/true` for the planned continuation; the original failed
runner, plan, log and conflict-state snapshot remain retained. No further
fixture or Git probe followed this result.

Root independently reviewed checkpoint two, request
`review-request-cc46e8c42b68487a89a55915cd034d56.json`, SHA256
`da10cc5069cf008dbafc86c24d2930b864300947f57dc360b6305328ad354a75`. Review
covered all four heads/trees, commit order, exact text/binary bytes,
rename/deletion/executable mode, evidence-before-cleanup, retained
clean-upstream change and declared conflict resolution. Root accepted refreshed
evidence and publication before the runner created the bare remote or pushed
Work refs.

The integrated actual shallow executor import retained its two approved commit
IDs and complete receiver history, without unrelated executor refs or receiver
shallow metadata. The richer deterministic fixture retained identity at
unchanged base, and retained authors/author dates/subjects/order and required
separate implementation/evidence and cleanup boundaries after both rebases.
Clean advanced-base rebase kept upstream content. Conflict halted before
publication; reviewer-owned resolution and fresh evidence review preceded its
publication. These richer artifacts came from a separate full-history fixture
sender, not from the actual tiny shallow executor model task.

Final local bare remote refs and receiver trees:

| Ref beneath `refs/heads/` | Final head | Final tree |
| --- | --- | --- |
| `master` | `73499b181812ca211cc3a7e46d668d1f550b4637` | Fixture selected base, unchanged |
| `work/delivery/integrated` | `dcc22b3f7596dc01789c8eac59531b2b0e669672` | `790d94b51b25b420d9cc7567ebf2f99b5b157367` |
| `work/delivery/unchanged` | `aabeba11af69c8d1cecc8487f212121f1775c739` | `c9ac5a471782eed9a0166113738bf0f32ffc6d0a` |
| `work/delivery/advanced` | `697c9f24f3854e4af032390f7abad200898f1b24` | `2cc674377fe15822aca1d3ff7d90a5676e3144be` |
| `work/delivery/conflict` | `065b070dfc099a8b5a6cb55b4b2be65383fefffe` | `045995a0e238b513af5736717b1dae3f54d4f962` |

Advanced commits are implementation/evidence
`74b3f463a2d8b854fd73e57f6f9482d812813cd3`, then cleanup
`697c9f24f3854e4af032390f7abad200898f1b24`, above
`8075babe4ee5c11a248d1ff49bac3ea76a3b3374`. Conflict commits are
implementation/evidence `4bfb2e3a7ed5d2c36f39eb77cfe70e2a3de0a30b`, then cleanup
`065b070dfc099a8b5a6cb55b4b2be65383fefffe`, above
`0d3d10559af80d20dbb1c34a97b4de5886b79c2e`. Each sequence remains two commits
with its expected base ancestry. Root independently verified the bare refs. The
publication remote intentionally hosts separate integrated/fixture histories;
this does not demonstrate a PR between those Work refs and its fixture master.

Recovery log `evidence/recovery-launch-46589f3a7e194d64a83bdda64c193ee5.jsonl`
has SHA256
`b3864b0e9651cc7f44818de1873a1f35d0f3437d85bfb103834c0e4ec57adb79`.
The original approved executor snapshot stayed identical, with no added remote,
alternates or recovered excluded objects; its auth/session state was untouched.
This preservation is not an actual sandbox replay after publication setup.

## Bounded recommendation and remaining acceptance

Use reviewer-accepted final executor commits as input: orchestrator explicitly
fetches only the approved assigned ref into its full-history repository,
reconciles/rebases onto the intended Work branch, preserves required commit
boundaries and refreshes invalidated evidence/references after rewrite. Complete
independent review before orchestrator-owned ready PR publication, then require
normal latest-head CI and maintainer review. Full-history reconciliation belongs
to the orchestrator; executor input/permissions need not gain publication
access. This selected path worked here; no production adoption or real PR is
performed.

Live GitHub/PR/CI and real-repository integration, missing-ancestry rejection,
format-patch/am/raw-diff comparisons, direct clone publication, rich artifacts
from the actual shallow model task and actual sandbox denial after publication
setup remain unrun. AC-1/AC-2/AC-3 remain TODO because the broader declared
Investigation coverage and alternatives are incomplete. No model, credential,
production root/source change or further trial is authorized by this result.
