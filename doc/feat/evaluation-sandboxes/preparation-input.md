# Preserved manual preparation input

Read for reconciliation, creation or enforcement. This supporting file preserves
useful historical/proposed instructions, not current guidance or authorization
to run them. It survives reconciliation-leaf cleanup; reviewed lasting guidance
belongs to one focused owner.

Source:
[manual procedure](https://github.com/msitarz/ataraxia/blob/31586c86f7bf7b77275dc7494964c57891678555/CONTRIBUTING.md#preparing-an-evaluated-fixture-clone)
and
[boundary controls](https://github.com/msitarz/ataraxia/blob/31586c86f7bf7b77275dc7494964c57891678555/doc/evaluation.md#prepared-clone-boundary-and-handoff)
at `31586c86f7bf7b77275dc7494964c57891678555`; frozen #315 comparison head is
`a8fd90ccb62f9593df499082e19a1a8c17eddb13`. The instructions below remain
available if those unmerged references cease to resolve. The
[verified preparation report](https://github.com/msitarz/ataraxia/blob/c9a24b3f8cccfb9392ec12db2029dfe03887786d/doc/feat/reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/environment-preparation/README.md)
supports only its Darwin Intel deterministic condition: no filtered-answer or
model-session proof, full effective environment capture, general host support,
setup-failure recovery or artifact-import proof.

## Native preparation input

Freeze selected committed input, source, absent final destination, executor
branch, tools/platform and configuration in the existing Work/protocol record.
Local `refs/heads/master` is the selected base unless explicitly instructed
otherwise. Uncommitted files are not clone inputs; source HEAD/status are
protocol-specific observations. Substitute recorded paths/branch consistently,
run each Git operation separately and stop on failure or mismatch. Reject an
existing destination, including dangling symlinks, before cloning.

Before the first Git operation, review and sanitize effective Git, uv, prek,
Python and shell configuration: remove inherited object/cache/environment paths,
includes, source hooks and credential-bearing settings; declare resolved tools
and required runtime reads. Recheck the selected ref before/after cloning and
compare clone HEAD with the full frozen commit ID.

```sh
git -C /source rev-parse refs/heads/master
git -c core.hooksPath=/dev/null clone --no-local --depth 1 --single-branch --branch master --no-tags /source /final/clone
git -C /source rev-parse refs/heads/master
git -C /final/clone remote remove origin
git -C /final/clone branch -m work/executor
git -C /final/clone rev-parse HEAD
git -C /final/clone rev-parse --is-shallow-repository
git -C /final/clone rev-list --count HEAD
git -C /final/clone show-ref
git -C /final/clone remote -v
```

The clone-only hooks override suppresses checkout hooks; never persist it,
disable installed hooks or alter host settings. Require frozen HEAD, shallow
`true`, count `1`, only assigned branch ref and no remotes/tags. Inspect absent
`.git/objects/info/alternates`, no source object hardlinks and effective Git
config without external object directory, hooks, includes or remote. Use
`--no-local` or reviewed `file://` shallow transport, without local/shared/
reference clone or full-history fallback.

Prepare online at the final location with no inherited virtual environment,
caches or source hooks, using reviewed sanitized configuration/resolved tools.
Canonical Make owns locked dependencies and pinned hooks.

```sh
cd /final/clone
make setup UV_CACHE_DIR=/final/clone/.cache/uv PREK_HOME=/final/clone/.cache/prek
make verify-setup UV_CACHE_DIR=/final/clone/.cache/uv PREK_HOME=/final/clone/.cache/prek
```

Inspect editable installs, resolved interpreter/symlink and hook launch paths,
and readable dependency/cache content for source/history, answers, credentials
and unintended external roots. Fresh caches alone prove no privacy property.
Preserve production signing. Retain partial destinations, diagnostics and failed
statuses for reviewed recovery, without overwrite, silent retry, installation
inside restricted execution or broader-access rescue.

## Boundary and handoff input

Freeze intended boundary, permitted files/references, scratch and required
tool/runtime reads. Keep reviewer records, controls and excluded answers outside
child access. Prohibited answers/evidence in the selected tree or indexes
require a reviewed fixture decision; do not silently filter committed input or
infer current-tree exclusion from shallow history. Record relevant effective
settings without retaining secrets/auth; uncaptured configuration remains a
limit.

Under the actual intended native restricted boundary, check useful prepared
tools and installed pre-commit/commit-msg hooks with clone-local scratch,
without installation/synchronization. Match unrestricted non-secret controls
with actual denied source-file/Git, old-object/local-fetch, source-symlink and
command-network probes. Absent origin/offline flags prove no denial. Unsupported
enforcement, failed/invalid controls, exposure, missing tools/hooks,
installation attempts or timeouts block handoff; retain outputs/statuses,
denials and deviations.

Bind handoff to exact input/branch, accepted setup/privacy/restricted readiness,
permitted reads/scratch, exclusions and unresolved limits. Runtime separately
rechecks its effective boundary at initial start and exact UUID resume;
preparation neither launches a model nor proves session isolation. Accepted
output/import retains independent review and evidence-before-cleanup gates.
