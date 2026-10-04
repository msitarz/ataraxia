# Historical access and commit batch

This deterministic batch extends the [protocol](protocol.md). Its first approved
host launch ran, but Git phases failed before Git startup. The corrected
Git-path retry also stopped at a runtime prerequisite; the separately frozen
runtime-read revision repeated the same blocker; this batch is now closed.
Earlier observations and raw logs remain intact. No model inference, network
server, transport/import or resume trial is included.

## Prepared fixture and controls

The new root is `/private/tmp/ataraxia-isolation-history-cb88dea8f876`.
Construction used the existing worktree cwd, isolated system/global Git config,
explicit fixture identity, signing disabled, empty construction hooks and a
noninteractive editor. Every Git operation ran separately and exited zero.
The source contains H0's historical canary, a distinct side-branch canary and an
H1 current canary; an uncommitted dirty file was added only after cloning.

| Revision | Frozen commit |
| --- | --- |
| H0, lightweight no-sign tag | `fe74a654b63a7da8eea0bb4a33d949b2d914fc67` |
| Side branch | `f94babc03e49cb823e8688ff5cd7fa4e359efb19` |
| H1, selected master base | `83bc8542fad85d7f49fc0205d578bf8c5e40bbbb` |

Five unrestricted controls exited zero: source revision resolution, reads of
H0 and side canaries, clone HEAD, and clone refs. Canary outputs were retained
as hashes, not printed. The depth-one `--no-local --single-branch --no-tags`
clone has only H1's master ref, H1's shallow boundary, no alternates or remote,
and no dirty input. A source-pointing symlink is deliberately present for the
denial probe. These checks are preparation evidence, not sandbox enforcement.

Construction, control logs, requested profile and frozen `batch-plan.json` are
in `evidence`, outside executor inputs. The profile retains the previous shape:
`:workspace` protections, root/temp/source denied, minimal runtime reads, clone
write, no command network and no approvals. Protected `.git` stays read-only;
staging and fetch can therefore fail at the Git write boundary by design.

## First reviewed runner

Runner: `evidence/history-probes.py` under the new root. SHA256:

```text
ee82f6c3b9f72fd823f9795b0e3e17bef8249b6b3c4ed2d0082316c2f72330ac
```

After independent review and exact host execution approval, planned invocation
from `/private/tmp/ataraxia-shallow-isolation` is:

```text
python3 /private/tmp/ataraxia-isolation-history-cb88dea8f876/evidence/history-probes.py
```

The runner checks frozen manifest/profile/hook hashes and fresh clone state,
then runs only the frozen sandbox argv. It records H0/side object absence before
and after explicit local H0/side fetch and unshallow attempts, direct source
file/Git-file/Git-show/symlink reads, and clone read/edit/check/stage/commit.
The fixture-owned pre-commit hook checks `task.txt` equals `ready` and writes
`hook-marker` containing `invoked`; it executes no external project hooks.
Commit requires successful staging, and hook invocation is observed separately.

Each command has a 30-second timeout; the entire batch has a shared five-minute
cap within the protocol's deterministic budget. Distinct exclusive-create JSONL
logs retain argv, statuses, diagnostics and output hashes. Launch failure,
timeout, source exposure or recovered objects stop execution. Failed staging
skips commit without changing permissions. No retries, escalation by the child,
bypass flags, cleanup or production changes are permitted.

Expected historical absence requires inspectable Git diagnostics and known
object controls. Fetch failure alone cannot establish source denial: distinguish
source-read diagnostics from protected `.git` write failures and other errors.
Direct read probes supply independent source-access evidence. Stage/commit/hook
failure is useful-work failure, not a reason to weaken protections. An exit-zero
runner is a mechanical summary; the orchestrator reviews the actual diagnostics
and artifacts before making any conclusion. Full candidate qualification and
AC-1/AC-2 remain unresolved until the wider Investigation is complete.

## First execution and corrected interpretation

The orchestrator approved and host-executed the first runner at 21:09:00–01 UTC.
It exited one. The immutable raw log is
`evidence/batch-launch-72d58aef34b9419c9476632432059d4e.jsonl` under the first
root. Every `/usr/bin/git` phase emitted
`xcode-select: error: No developer tools were found` before Git ran. The runner
incorrectly labeled these nonzero results `object_absent=true` and continued
after an unsupported tool boundary. Those labels are invalid: object absence,
source Git access, fetch/unshallow and staging are **inconclusive**. Staging did
not demonstrate protected Git-write denial. Commit and hook remain unrun. Raw
records were not changed.

Actual `cat` commands independently denied current-source, source `.git/HEAD`
and source-symlink reads with Operation not permitted and empty stdout. Clone
read/edit/check succeeded. These limited observations do not qualify a
candidate.

## Fresh tool-preparation correction

Read-only inspection found PATH Git `/usr/local/bin/git`, resolving to
`/usr/local/Cellar/git/2.55.0/bin/git`, version 2.55.0, with helper path
`/usr/local/opt/git/libexec/git-core`. This was the Git used by successful
fixture controls, rather than the forced system shim. `otool -L` identified
non-system dependencies `/usr/local/opt/pcre2/lib/libpcre2-8.0.dylib` and
`/usr/local/opt/gettext/lib/libintl.8.dylib`, plus system libraries/frameworks.
Their availability through the unchanged minimal-read profile is untested. If
unavailable, report the exact binary/helper/library path; do not grant broad
reads or modify the profile without review. No installation or global changes
ran.

A fresh independent source/clone at
`/private/tmp/ataraxia-isolation-git-retry-18092082117a` was reconstructed from
the first source’s committed snapshot, preserving the same H0/H1/side IDs. Old
fixtures were not modified. Five separate construction Git operations passed.
Four fresh unrestricted controls read H0/side canaries, read H1 as `commit`, and
obtained the actual H0 missing-object diagnostic:
`fatal: git cat-file: could not get object info` (exit 128). The new clone has
H1’s shallow boundary, no alternates/remote or dirty input, and the same vetted
hook. Raw control and construction logs are retained under its `evidence`.

The new frozen manifest pins the concrete Git executable/helper path and keeps
child profile restrictions unchanged. Sandboxed version and readable-H1 sanity
checks now precede object probes. Any runtime/startup/repository-discovery
failure is inconclusive and stops execution. Object absence requires the actual
Git missing-object diagnostic and successful H1 control, not merely a nonzero
exit. The five-minute shared cap and 30-second per-command limits remain.

The Git-path correction runner is `evidence/history-probes.py` under the new
root, SHA256:

```text
ecdf5663c5f25fd33fda8a8c22bc5f7fdb20af296b4ca0c6ae02e8cd9a5df89d
```

After independent review and specific host launch approval, invocation from
the existing worktree cwd is:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/history-probes.py
```

This fresh correction retains the first observation; it does not replace it. Its
later runtime-only result is retained below; no model trial or AC completion
follows.

Independent review made directory-discovery handling phase-aware: explicit
source-directory Permission denied or Operation not permitted is an intended
source-denial diagnostic. The same discovery failure outside source phases
stops execution. Generic not-a-Git-repository failures and actual sandbox,
Xcode or dynamic-loader startup failures remain inconclusive and stop. Frozen
argv, manifest and profile were not changed by this correction.

## Runtime-read revision and batch closeout

The orchestrator’s second specifically approved host launch exited one at
21:14:40 UTC. Its immutable log under the retry root is
`evidence/batch-launch-21c804b9da6a43118de1ae4f2a209d69.jsonl`. Only version
ran: exit 134, `dyld: Library not loaded`, with the pcre2 library explicitly
blocked by sandbox. This is a runtime dependency access failure, not the prior
generic sandbox-application failure. All later phases remain unrun.

The same untouched clone was verified to retain pending task, H1 shallow
boundary and the frozen hook hash. No new fixture was necessary. Existing
configurations, manifests, runners and logs were left unchanged. A separate
`evidence/runtime-read-r1` contains the revised manifest/profile/state/runner.
It declares only these exact tool-resource **read** paths:

```text
/usr/local/opt/pcre2/lib/libpcre2-8.0.dylib
/usr/local/Cellar/pcre2/10.48/lib/libpcre2-8.0.dylib
/usr/local/opt/gettext/lib/libintl.8.dylib
/usr/local/Cellar/gettext/1.0/lib/libintl.8.dylib
/usr/local/opt/git/libexec/git-core/git-upload-pack
/usr/local/Cellar/git/2.55.0/libexec/git-core/git-upload-pack
/usr/local/Cellar/git/2.55.0/bin/git
```

Read-only symlink/dependency inspection grounded these opt and resolved paths;
the two libraries link only to already-declared system libraries/frameworks.
The local-fetch helper resolves to the pinned Git binary. Resource hashes are
frozen and checked before launch. There is no broad Homebrew/Cellar grant.
Source/root/temp denial, command network denial and Git write protections remain
unchanged. This revision declares necessary runtime resources; it does not
relax the source/history invariant or permit protected Git writes.

The revised runner retains identical probe argv, version/H1 gates, five-minute
batch cap and 30-second command limits. Remaining runtime blockers fail closed.
Its reviewed SHA256 is:

```text
a9ddeb0d8b3d40e49866be6008018f6c7f4ac66b25bceb6d5bd757fa49f0e7f4
```

After independent review and exact host launch approval, planned invocation
from the existing worktree cwd is:

```text
python3 /private/tmp/ataraxia-isolation-git-retry-18092082117a/evidence/runtime-read-r1/history-probes.py
```

No model inference, installation, cleanup or production change ran.
Earlier inconclusive results remain preserved.

At 21:19:26 UTC, the orchestrator specifically approved and host-executed the
runtime-read revision. It exited one. The retained log is
`evidence/batch-launch-9b35e0f615734167840a58ff02ab0fe6.jsonl` under the retry
root. Preflight hashes passed; only runtime-version ran, exiting 134 with the
same pcre2 library blocked by sandbox despite the exact read grants. All later
phases were unrun. The runner’s summary correctly retained an unsupported
runtime prerequisite rather than declaring object absence or source denial.

Three actual history launch batches are retained: system shim, pinned Git, and
exact runtime-read revision. The first supplied independent cat/read/edit
outcomes but its Git labels were invalid; the later two stopped at runtime. The
same runtime finding remained after one correction, so this batch stops under
the
[orchestrator correction rule](../../../../../../orchestrator.md#review-and-return).
No further profiles, probes or exploration are authorized by this closeout.

The current host filesystem boundary supports clone file edits and direct
source/Git-file/symlink read denial. It cannot qualify useful Git work.
Historical-object/fetch checks and staging remain inconclusive; commit/hook
and resumed/custom-agent work remain unrun. Protected `.git` write denial is
documented expected behavior, **not observed evidence in these runs**. There
is no performance/model conclusion, AC-1/AC-2 completion or policy adoption.

The next reviewed decision is whether to diagnose effective-profile selection,
symlink resolution or runtime metadata with bounded inspection and no broader
grants, or use a separate supported runtime/environment. The exact underlying
cause is unknown; neither path is implemented or adopted here. Old profiles,
manifests, runners and raw logs are unchanged.

The user subsequently authorized a bounded
[runtime diagnosis](runtime-diagnosis.md), without broader grants. It retains
the stopped batch and does not authorize further history/model trials.
