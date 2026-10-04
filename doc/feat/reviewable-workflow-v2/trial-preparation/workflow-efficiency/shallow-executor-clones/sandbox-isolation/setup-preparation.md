# Project setup preparation

The user authorized deterministic project setup before preparing an actual
executor/resume trial. No setup sandbox, dependency installation or model call
has run. Initial preparation stopped at cache vetting; continued preparation
below now provides a separately frozen selected-cache/runtime condition.

## Fresh frozen input

The original repository's current `master` was verified as
`6c8720287aa121592ba2b3506221593b182c70f8`. A new depth-one, single-master,
no-tags, `--no-local` clone is retained at
`/private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/clone`.
Its HEAD and shallow boundary match that revision; origin was removed, no
alternates exist, and no `.venv` or cache was copied. Parent worktree edits are
not inputs. Git construction used disabled global/system configuration,
noninteractive choices and disabled inherited hooks. No existing fixture was
reset, reused or cleaned.

## Observed prerequisites and blocker

`make help`, CONTRIBUTING, engineering and validation guidance were read.
The contracts require fresh locked offline `make ci-setup UV_OFFLINE=true`,
`make verify-setup`, focused checks through Make, and installed pinned hooks.
The copied worktree cache is available but cannot yet be declared vetted.
Its inventory contains 76 Ataraxia package/editable artifacts, 35 metadata files
with original-source or disposable-worktree path references, 12 symlinks whose
resolved targets leave the cache, and three third-party hook Git repositories.
References alone do not establish readable prohibited answers; they require
selection and inspection before exposing the cache to the child. Third-party
hook repositories are dependency inputs, not proof of Ataraxia history leakage.
No raw `.cache`, rumdl result cache or existing `.venv` was copied.

Full paths, symlink targets, relevant metadata hashes and clone checks are in
`/private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/evidence/cache-inventory.json`.
Inventory SHA256:
`d696be8658f7e2ded2c5340a9e2e18b1267a3f7baed1422d9bb94a386dc665e3`.

Available uv resolves to `/usr/local/Cellar/uv/0.12.19/bin/uv`, within the
tested `/usr` read concession. Python 3.14 resolves to
`/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14`, outside
that allowance. Its runtime resources and any required scratch roots must be
declared as a separate reviewed condition; no broad `/Library` or temp grant
has been added. Neither offline cache completeness nor sandbox startup has
been established.

## Concrete next preparation

Select dependency-only uv artifacts, excluding Ataraxia editable/build outputs
and source-path caches; inventory retained links and metadata. Separately vet
pinned hook sources/environments for relocatability and declared Python reads.
Freeze those selected bytes, exact runtime paths, profile, Make commands and
control destination before host launch. Preserve source/root/temp denies,
clone Git writes, network disabled and approval never; do not automatically
expand permissions on failure.

The proposed deterministic runner will stop on the first unsupported runtime,
invalid control, missing cache or timeout. Each setup command is bounded to
five minutes, with 15 minutes shared total. It will run locked offline setup,
readiness and focused checks, and exercise vetted installed hooks through
repository Make contracts. A separate fresh empty-cache destination will
observe recoverable setup failure without cleanup, reset or full-history
fallback. Both successful and missing-cache outcomes remain unrun.

Only after this gate completes should standalone B's model phase freeze the
exact installed GPT-6.1 Sol model identifier at low effort, initial/resume
prompts, one initial and one resumed turn, shared budget, denial checks and
reviewer-owned evidence for approval. No model dispatch is authorized by this
preparation artifact. AC-1/AC-2 remain TODO; no policy is adopted.

## Selected-cache condition ready for review

Continued authorized preparation created a new `dependency-snapshot` under the
setup fixture, leaving the raw cache unmodified. Selection retained only
registry wheel versions in the frozen `uv.lock`, plus hook dependencies uv
0.12.19, ruamel-yaml 0.19.1 and setuptools 84.0.0. Archive targets and HTTP
wheel metadata retain their cache layout. No local sdists, Ataraxia archives,
interpreter metadata, existing environments, config tracking or result caches
were copied. Selected bytes have named input provenance and per-file hashes.

The two retained third-party hook repositories have matching local FETCH_HEAD
tag/origin evidence and detached HEADs: uv-pre-commit 0.12.19 at
`2aeb804518b4373dbf5adb8dddc5466d9a6e6b21`, and pre-commit-hooks v6.0.0 at
`3e8a8703264a2f4a69428a0aa4dcb512790b2c8c`. Neither has alternates. The snapshot
contains 2,937 files and 42 internal links; a byte scan found no original-source
or disposable-worktree path references, and no links resolve outside it.
This is bounded local provenance, not fresh upstream signature verification.
Hook environments will be rebuilt through `make setup`, not rewritten.

`evidence/dependency-snapshot.json` SHA256 is
`f1af22bd667a699fbe502195cdaa38d00542f5c50d505573c5437a97d0554b89`.
The selected snapshot was copied into the fresh clone's `.cache`; `.venv`
remains absent. A second independent shallow `missing-cache-clone` at the same
base has no cache or environment and retains no origin. Both have clone-local
`.scratch/tmp` directories; nothing was reset or cleaned.

Separate frozen artifacts are under
`/private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/evidence/setup-condition`.
The condition preserves root/temp/source denies, entire `/usr` read, clone Git
writes, inherited protected `.codex`, network disabled and approval never.
It additionally declares read access to the contents of exactly
`/Library/Frameworks/Python.framework/Versions/3.14`, and writes to the two
fresh clones, including their local scratch/cache roots. This is a new runtime
resource condition, not evidence that r5 alone supports setup. No broad
`/Library` or temp grant was added.

Profile SHA256:
`cc1044b4074afa21cea32bde9925eb9888e6921bcdca5bf48c91c58abc3ebc30`. Plan SHA256:
`bbce1c5ac2d4c6458345369872b74209c93d42b2a3519bea8c78ce00af01c1a8`. Runner
SHA256: `a140bf9aa88c28b6382319afc51137492fafa45183a203e782da7aabcdf6a0fa`.
Python syntax validation passed. The first approved launch is retained below.

After independent review and specific host execution approval, invoke from the
existing worktree:

```text
python3 /private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/evidence/setup-condition/setup-probes.py
```

The runner verifies frozen hashes, internal links, fresh environments and base
before uv/Python startup controls. Runtime gates have 30 seconds; Make commands
have five minutes each within 15 minutes total. It runs `make setup
UV_OFFLINE=true`, `make verify-setup`, `make verify-check` (including actual
pinned hook execution), and focused `make test
ARGS=test/unit/test_acceptance_coverage.py`. Installed pre-commit/commit-msg
hook files are then checked. All preparation executes inside the child profile;
there is no unrestricted hook preparation that could fetch unexpectedly.
Offline backend/hook completeness is established only if these steps pass.

Only after selected-cache success does the separate empty-cache clone attempt
offline `make ci-setup`. A recognized offline/cache failure is retained as
recoverable; runtime/permission failures are inconclusive. The first failed
positive gate or timeout stops, with no fallback grant, cleanup or model call.
The existing raw-cache blocker remains part of the preparation history.

## First launch and GNU Make correction

The orchestrator reviewed and specifically approved the first host launch. It
exited one at 06:38 UTC on 2026-10-04; the unchanged raw log is
`/private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/evidence/setup-condition/launch-6d0fc9ed5c164c349c8c81abce4fb5cd.jsonl`.
uv and Python startup passed. `/usr/bin/make` failed in xcode-select before
setup ran. This is a tool-startup failure, not dependency-cache or sandbox setup
evidence. Both destinations still have fresh absent `.venv` directories.

The orchestrator's ordinary control found GNU Make 4.4.1 at
`/usr/local/bin/gmake`. The separate `evidence/setup-gmake-r1` condition pins
its resolved executable `/usr/local/Cellar/make/4.4.1/bin/gmake`, SHA256
`64311ae3e12415a2893692af0849aea74d8c9f6df116753bdeec8496b514fca1`. The profile
is byte-identical and fixture/cache inputs are retained. This changes only the
Make executable and adds a 30-second GNU Make startup gate; the same repository
targets run, including recursive `$(MAKE)` inheritance. No grant, installation,
fixture reset or model call was added. A repeated startup finding stops rather
than triggering another automatic correction.

New plan SHA256:
`5e203bb2f3fcbb721e8dfe16de42e15603e3133529910999929ca68f40ef32cf`. New runner
SHA256: `c810d31f0938af66c8093e3f12b88d5359ad71d11ef870132449135870911de8`.
Syntax validation and fresh-environment guards passed during preparation. The
corrected launch outcome is retained below. After independent review and
specific host execution approval, invoke from the existing worktree:

```text
python3 /private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/evidence/setup-gmake-r1/setup-probes.py
```

## GNU Make launch and hook-cache layout correction

The approved GNU Make launch exited one on 2026-10-04 at 06:45:59–06:46:03 UTC.
Its immutable log is
`/private/tmp/ataraxia-isolation-setup-7a26d72bb1c7/evidence/setup-gmake-r1/launch-216e7d97e5e540a0b4ee660836a53e61.jsonl`.
uv, Python and GNU Make startup passed. Locked uv sync created a fresh virtual
environment, built Ataraxia and installed 40 packages. Hook preparation then
failed resolving uv for uv-lock: the cache lacked uv at the active location,
with networking disabled. Readiness, hook execution, focused tests and the
missing-cache case remain unrun. Partial dependency setup success does not
establish full project setup compatibility.

The runner sets inherited `UV_CACHE_DIR` to the clone's root `.cache/uv`, while
selected hook wheels had been stored under `.cache/prek/cache/uv`. This was a
new cache-resolution finding, distinct from the previous system-make startup
failure. Active cache placement was a hypothesis, not an established cause. A
separate layout-only correction mirrors the already-vetted uv 0.12.19,
ruamel-yaml 0.19.1 and setuptools 84.0.0 registry wheels and their archive
targets into the selected root uv cache. Hook source metadata declares
uv==0.12.19 and ruamel.yaml>=0.15; pre-commit-hooks uses setuptools. Its tomli
requirement is conditional on Python below 3.11 and does not apply here. No
additional network artifact or cached hook environment was imported. Remaining
backend/dependency completeness will be tested, not assumed.

The new fixture is
`/private/tmp/ataraxia-isolation-setup-hookcache-9d90aa43928b`.
Both fresh independent depth-one clones select the same master base, have
origins removed and absent `.venv` directories. The old partial setup remains
untouched. The new snapshot contains 3,334 hashed files and 45 internal links,
with no detected source/worktree byte references or external resolved links.
Snapshot SHA256:
`c0ab93c12bc381683c2c195c99c224c31725a26f44f2926e4639ed462c432372`.

The profile maps writes to the fresh clone paths, retaining identical access
semantics: explicit clone Git writes, entire `/usr` read, exact Python 3.14
framework read, source/root/temp denies, network disabled, approval never and
clone-local scratch. No permission grant changed. Profile SHA256:
`4a9149b9a2cdfcd1f5c8405b3212499a4635a336144bc252d389e8e412c929ba`. Plan SHA256:
`ce369fb697543b97035cbf2fd05478312e8c05f5ba4186d99dc82b8fd84b69f5`. Runner
SHA256: `8ab55b68c4e2de26855e4624d28ac9188bfd3eac5e4c6de1478e1d3a273da9c2`.

The same frozen Make workflow, runtime gates, fresh-environment/hash guards and
five-minute command/15-minute shared limits apply. Syntax validation passed; the
corrected launch outcome is retained below. After independent review and
specific host execution approval, invoke from the existing worktree:

```text
python3 /private/tmp/ataraxia-isolation-setup-hookcache-9d90aa43928b/evidence/setup-hookcache-r1/setup-probes.py
```

If the cache finding repeats after this single correction, stop and report;
there is no automatic cache expansion, grant rescue or model dispatch.

## Repeated hook-cache finding and stop

The orchestrator reviewed and specifically approved the fresh cache correction.
It exited one on 2026-10-04 at 06:54:21–06:54:25 UTC. Its immutable raw log is
`/private/tmp/ataraxia-isolation-setup-hookcache-9d90aa43928b/evidence/setup-hookcache-r1/launch-0a6f9bc1be9d40d39df70e8fd40b689c.jsonl`.
All runtime gates passed. Locked uv sync again created a fresh environment and
installed 40 packages. uv-lock hook preparation again failed with uv not found
in cache while networking was disabled. Readiness, actual hook execution,
focused checks and the missing-cache case remain unrun.

The placement correction did not resolve the finding. The hook subprocess's
actual effective cache identity and resolution requirements were not captured;
package/archive presence alone does not prove usable index metadata, platform
provenance or resolver visibility. The earlier active-cache explanation remains
an unproven hypothesis. No permission or network denial is inferred from this
cache-resolution error, and partial uv sync success does not qualify full setup.

The repository's
[orchestrator repeat-stop rule](../../../../../../orchestrator.md#review-and-return)
says: "If the same finding remains after a correction attempt, or the session
cannot continue, stop and report attempts, current evidence, and the specific
decision or help needed." The same finding persisted after the single cache
correction, so this batch stops. Old logs, profiles, snapshots and partially
prepared destinations remain unchanged; no further inspection, grant, cache
revision, trial or model preparation followed.

The next decision requires orchestrator or maintainer steering: authorize a
bounded read-only cache-resolution investigation of effective hook
`UV_CACHE_DIR`, registry/index metadata and platform/cache provenance, or retain
this partial compatibility finding without expanding the investigation. There is
no automatic retry or network fallback. Setup preflight is unmet, so the actual
executor/resume phase remains unprepared and unrun. AC-1/AC-2 remain TODO; no
policy is adopted.

## Authorized online host preparation pending review

After the repeated finding, the maintainer authorized a new direction: prepare
actual pinned hooks online outside the child sandbox in a dedicated cache, then
recreate a fresh environment offline. This is new steering, not an automatic
retry of the failed layout correction. No online launch or model call has run.

Read-only inspection of the retained diagnostic confirms the hook subprocess
command was `uv pip install --project / --directory <hook-repository> .`.
The runner's declared `UV_CACHE_DIR` points to root uv cache, but the diagnostic
does not dump the subprocess's effective environment or resolver index state.
Wheel-only selection omitted registry/simple-index metadata. That omission is
a plausible explanation, not established causality. The new online preparation
preserves the complete generated cache before any subsequent selection.

Fresh fixture: `/private/tmp/ataraxia-isolation-online-c44d9fef9c6a`. Its
`host-clone` is an independent depth-one no-tags master clone at the same
approved base with origin removed and no alternates. No existing environment or
cache was copied. `dedicated-cache` is empty. Old attempts remain untouched.
Pinned GNU Make 4.4.1, uv 0.12.19, Git 2.55.0 and the existing Python 3.14
binary are recorded by resolved paths/hashes, alongside Makefile/lock/hook input
hashes.

The runner runs startup controls, `make setup`, `make verify-setup` and
`make verify-check` using pinned GNU Make. Recursive Make inherits that binary.
Startup commands have 30 seconds; Make commands have five minutes each within
15 minutes total. It removes inherited uv/pip/proxy/config overrides, disables
Git credential helpers and global/system Git config, disables Python downloads,
uses the exact existing Python interpreter, and explicitly selects the public
PyPI index. uv user configuration is disabled. It does not invoke authentication
commands, model sessions or source-repository fetches; the clone has no remote.
Permitted preparation fetches are locked registry dependencies/build backend,
pinned hook sources uv-pre-commit 0.12.19 and pre-commit-hooks v6.0.0, and their
declared build/runtime dependencies. Actual resolved versions and provenance
must be inventoried before becoming frozen offline inputs. Registry/CDN and
pinned GitHub source URLs are declared in the plan, not a transport allowlist.

A completed run inventories every generated cache file/hash, symlink target,
source-reference file, environment metadata and dependency Git origin/revision/
FETCH_HEAD/alternates, preserving resolver metadata. This raw cache is not
approved executor input. Later filter-on-copy must exclude project editable
artifacts and old environments while preserving dependency index metadata and
vetting links; no raw-cache deletion or blind metadata patch is planned. The
offline profile/runner will be prepared only after the actual online result is
available, preserving prior child permission semantics and fresh destinations.

Plan SHA256:
`b46e0ca0d34f924d40fc9f39b184adb1582635f1c8c8df338497750ddab1129a`.
Runner SHA256:
`0045b0d76003c12757fe3898641158cc580e731af3572612d0dd4ff9d0637140`.
Syntax validation passed. After independent review and specific networked host
execution approval, invoke from the existing worktree:

```text
python3 /private/tmp/ataraxia-isolation-online-c44d9fef9c6a/evidence/online-prepare.py
```

One consolidated correction is permitted for this direction; a repeated finding
then stops and returns for steering. No installation/network action has been
executed by the leaf, no production Make target changed, and model/resume
preparation remains gated on actual setup compatibility.

## Online result and frozen offline recreation

The orchestrator independently reviewed and approved the online host runner. It
exited zero; `make setup`, `make verify-setup` and `make verify-check` passed,
including prepared/installed pinned hooks and static checks. Tracked inputs were
unchanged. The immutable log is
`/private/tmp/ataraxia-isolation-online-c44d9fef9c6a/evidence/online-launch-09b9619f3b174521b8bbbf288ae955af.jsonl`.
The full dedicated-cache inventory has 3,308 files and 58 source references,
SHA256 `6451b912dbc953058ee49527c9f66a81e015d8256c4ded004dabd840e5142cc1`, at
`evidence/online-cache-inventory-09b9619f3b174521b8bbbf288ae955af.json` under
that fixture. No original cache was mutated and no model ran.

Read-only inventory inspection confirms hook dependencies were generated under
`prek/cache/uv`, including `simple-v25/pypi/uv.rkyv`, `ruamel-yaml.rkyv` and
`setuptools.rkyv`. Earlier selected snapshots omitted these registry records.
That omission is established; its causal sufficiency remains untested. Hook
cache generation at this location does not prove every prior subprocess's
complete effective cache state. No opaque resolver metadata was rewritten.

A fresh offline fixture is
`/private/tmp/ataraxia-isolation-offline-c2afe48e926a`.
Its two independent depth-one, no-tags clones use the same approved master
base, with origins removed and no alternates. No `.venv` was copied. Filter-on-
copy retained registry wheels/archives, complete corresponding simple-index
and HTTP metadata, and the two pinned dependency Git repositories. It excluded
Ataraxia editable archives, all local-path sdist caches and their archive
outputs, hook environments, interpreter metadata, logs/tracking/workspace
results and source-reference files. The raw online cache remains untouched.

The selected snapshot has 3,041 hashed files and 42 internal links, with no
original/online source path references detected in selected bytes and no links
resolving outside the snapshot. Its per-file provenance, exclusions, retained
resolver records and dependency origin/revision/alternates evidence are frozen
in `evidence/dependency-snapshot.json`, SHA256
`6e2ee5eed6a1d7da896566e625b0d294b1a44fac538f53df220260e01775255d`.
Fresh hook environments and Ataraxia builds will be recreated through Make.

The offline condition maps only the fresh clone paths, retaining the prior
permission semantics: root/temp/source denies, entire `/usr` read, exact Python
3.14 framework read, clone Git writes, local scratch, network disabled, approval
never and inherited `.codex` protection. It matches online's pinned tool PATH,
`UV_NO_CONFIG=true`, explicit `UV_DEFAULT_INDEX=https://pypi.org/simple` and
disabled credentials/proxy overrides, adding `UV_OFFLINE=true`. This
environment/index condition is declared separately from earlier attempts.

Profile SHA256:
`854e52e4c7d5aac1897550daa80b8a728b897e60c767c090c710621c86846d31`. Plan SHA256:
`d14c38c8308abf1d7fbe7e749d17badbb8316aa939ba96276f45637a034ce7a7`. Runner
SHA256: `b266219510fe2d42da305d9d3fa26fc17d9c62477426498651638c0470d7e86a`.
Syntax validation passed; the offline runner has not executed. After independent
review and specific host execution approval, invoke from the existing worktree:

```text
python3 /private/tmp/ataraxia-isolation-offline-c2afe48e926a/evidence/offline-recreation/setup-probes.py
```

The runner checks frozen hashes, links, base and absent environments, then
30-second uv/Python/GNU Make gates. Five-minute commands within 15 minutes total
run offline setup, readiness, full static/hook checks and the same focused test.
Only after positive success does the separate empty-cache clone attempt offline
ci-setup, requiring a recognized cache/offline diagnostic and no runtime or
permission error. First invalid gate/timeout stops with retained destinations;
one consolidated correction at most, followed by repeat-stop. Model/resume
preparation remains pending actual offline compatibility evidence.

## Offline recreation result: setup passes, static gate stops

The independently reviewed and approved offline host launch exited one. Its
immutable log is
`/private/tmp/ataraxia-isolation-offline-c2afe48e926a/evidence/offline-recreation/launch-eff2bfaf40bd47ef9464a1869e68e323.jsonl`.
Runtime controls passed. Offline `make setup` created a fresh environment,
installed the locked 40 packages, rebuilt hook environments, installed both Git
hooks and built the wheel. `make verify-setup` passed without changes. Thus full
offline setup and readiness succeeded under this declared cache/index/runtime
condition. The previous hook resolver blocker did not recur; this multi-part
condition does not isolate which change caused recovery.

`make verify-check` passed the actual check-yaml, check-merge-conflict and
private-key hooks, and Ruff lint. The nonblocking size advisory reported two
functions. Ruff format-check then failed traversing clone-local `.scratch/tmp`
with Operation not permitted; 120 files were already formatted. Remaining
static checks, the focused test and the separate missing-cache case are unrun.
Full static compatibility and the model preflight are not established. The
batch stopped; no corrected runner, grant change, retry or model followed.

Bounded read-only inspection found `.scratch` and `.scratch/tmp` are ordinary
0755 directories, not links; tmp was empty and resolved to its literal path.
The launcher sets `TMPDIR` to that directory while the profile declares
`:tmpdir = deny`. At the matching Codex revision,
[Tmpdir resolution reads launcher TMPDIR directly](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/protocol/src/permissions.rs#L2268).
The
[Seatbelt read builder excludes narrower denied subpaths](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/sandboxing/src/seatbelt.rs#L541)
from permitted roots. Therefore the declaration targets the scratch path rather
than an unrelated host temp path. This source-backed configuration collision is
consistent with the traversal denial; effective Seatbelt output and the precise
failing syscall were not captured, so full runtime causality remains inferred.
It is not a cache-resolution or formatting-content failure.

Next steering must choose a separately reviewed launcher/profile condition
that preserves denied host temp access while making declared clone-local
scratch usable, or retain this remaining static limitation. No new condition
is implemented here. Project setup/readiness evidence stands independently;
remaining checks and executor/resume stay gated. AC-1/AC-2 remain TODO and no
production policy is adopted.

## Authorized launcher scratch correction pending review

Maintainer steering authorized one bounded scratch-mapping correction and
another offline check batch. A fresh fixture is retained at
`/private/tmp/ataraxia-isolation-scratch-d388fe8a28bd`.
Its two independent depth-one no-origin clones select the same approved base.
Fresh environments remain absent. The successful online-derived selected
snapshot was copied unchanged; no previous partially prepared destination was
modified or cleaned. Its manifest SHA256 remains
`6e2ee5eed6a1d7da896566e625b0d294b1a44fac538f53df220260e01775255d`.

Read-only matching source confirms the
[Seatbelt policy arguments are constructed before child spawn](https://github.com/openai/codex/blob/01fc69f4026735edfdf6789820549727a4867b11/codex-rs/cli/src/debug_sandbox.rs#L399).
Together with the Tmpdir resolver above, this supports separating the launcher
variable from the later child runtime variable without changing policy grants.
The launcher retains and guards its original host TMPDIR:
`/var/folders/ml/0n6wj9mx44d35kqdktzmm7k40000gn/T/`.
The frozen profile still denies `:tmpdir`, host/root/source/temp access, and
preserves prior `/usr` and exact Python reads, clone/Git writes, disabled
networking and approval never. Only fresh clone paths are remapped.

Each sandbox command now prefixes its actual tool with `/usr/bin/env
TMPDIR=<that-clone>/.scratch/tmp`. Thus profile expansion sees the original host
temp path, while the already-sandboxed env process sets allowed clone-local
scratch for tools. No host temp grant or broad temp allowance is added. A
30-second scratch read/write control precedes runtime/setup gates. This source-
backed launcher hypothesis remains subject to actual execution; no probe ran.

Profile SHA256:
`d872dd60423c67f3f8dbbd9daf8ad19f8057f60d9ef967996c2729c1c114c901`. Plan SHA256:
`4dde19b42a5a3142f57f1ed15ac791ab31cd218026c454f3eb337cd138359f3d`. Runner
SHA256: `bd0b69dfc772539edbe2bfa5e443094e65b3ba4f9127c7eb3d078b9b185a6e50`.
Syntax validation passed. After independent review and specific host execution
approval, invoke from the existing worktree:

```text
python3 /private/tmp/ataraxia-isolation-scratch-d388fe8a28bd/evidence/scratch-r1/setup-probes.py
```

The same frozen offline setup/readiness/full-static/focused-test/missing-cache
workflow and 30-second runtime/five-minute Make/15-minute total limits apply.
First invalid gate or timeout stops; there is no automatic further correction,
permission rescue, network fallback or model dispatch.

## Completed scratch-corrected offline compatibility

The orchestrator independently reviewed and specifically approved scratch-r1's
host launch. It exited zero. The unchanged complete log is
`/private/tmp/ataraxia-isolation-scratch-d388fe8a28bd/evidence/scratch-r1/launch-b73a3ccc61904c11b73d225a0dcac6de.jsonl`.
Scratch read/write and all runtime gates passed. Offline setup, readiness and
full static verification passed, including actual pinned hooks. The focused
selection passed all 16 tests. The separate empty-cache destination exited two
with a recognized offline missing-pyrefly-artifact diagnostic, without runtime
or permission failure; the recoverable destination was retained.

This completes the deterministic project setup prerequisite under the frozen
online-derived dependency snapshot, explicit Python/framework/index condition
and launcher/child scratch separation. The condition keeps Codex's original
host TMPDIR for policy expansion and changes TMPDIR only through sandboxed env
for tool execution. No broader temp grant, permission rescue or network fallback
was introduced. Prior incomplete attempts and failed hypotheses remain retained.

This batch did not repeat host-temp/source/network denial probes; those
boundaries are not newly established by successful setup checks. Earlier
bounded denial evidence retains its original conditions and limitations.
Actual model execution/resume, custom-agent verification and the reviewed
Investigation recommendation remain unrun. Setup readiness is now met, but
AC-1/AC-2 remain TODO and no production policy is adopted. No model preparation
or additional probe followed this result; a later reviewed handoff owns that
next phase.
