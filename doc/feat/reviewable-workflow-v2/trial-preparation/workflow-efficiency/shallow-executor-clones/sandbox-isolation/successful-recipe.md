# Reproduce the tested standalone sandbox condition

This is the retained successful macOS condition, not a production sandbox or a
new authorization to dispatch models. The
[actual executor/resume result](standalone-model.md#completed-standalone-b-actual-executor-and-resume)
and [committed audit](audit/README.md) establish what ran. Deterministic full
project setup and the tiny model task are separate demonstrations; no full
project model task ran. Preserve every failed attempt when changing a condition.

The maintainer explicitly requested one preservation commit with all findings,
evidence and instructions, followed by normal PR review, with no cleanup commit
yet. This authorizes the larger preservation review surface as a scope
exception. Contracts/remaining criteria stay TODO; no completion or policy
adoption is inferred. No production Make target changes accompany this recipe.

## Freeze tools, input and fresh destinations

On the tested host: Codex 0.159.3, Git 2.55.0, GNU Make 4.4.1, uv 0.12.19 and
Python framework 3.14. Pin concrete resolved executables and SHA256 in the new
reviewer manifest; version match alone is insufficient. A different executable,
platform, path or cache is a new reviewed condition. The source comparison found
0.160.0's relevant permission implementation unchanged, not a tested upgrade.
Homebrew alias reads failed under narrower runtime grants; entire `/usr` read
is the explicit concession of this successful condition.

Choose paths in a reviewer-owned fresh root, outside the source and every old
fixture. These are examples to adapt and freeze, not paths to reuse:

```sh
TRIAL_SOURCE=/absolute/reviewer/source
TRIAL_ROOT=/private/tmp/fresh-reviewer-chosen-name
TRIAL_CLONE="$TRIAL_ROOT/clone"
TRIAL_STATE="$TRIAL_ROOT/state"
TRIAL_EVIDENCE="$TRIAL_ROOT/evidence"
TRIAL_BASE=reviewer-recorded-full-commit-id
TRIAL_GIT=/usr/local/Cellar/git/2.55.0/bin/git
TRIAL_MAKE=/usr/local/Cellar/make/4.4.1/bin/gmake
TRIAL_UV=/usr/local/Cellar/uv/0.12.19/bin/uv
TRIAL_PYTHON=/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14
```

Reject an existing root/destination; never reset/clean it. Record selected
source master HEAD and require it equals TRIAL_BASE before construction and
launch. Historical project-setup base was
`6c8720287aa121592ba2b3506221593b182c70f8`; the tiny fixture's different H1 is
recorded in its model plan. Do not substitute either ID into another repository.
Run each Git operation separately, without chained shell operators:

```sh
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null "$TRIAL_GIT" -C "$TRIAL_SOURCE" rev-parse refs/heads/master
mkdir -m 700 "$TRIAL_ROOT"
mkdir -m 700 "$TRIAL_STATE" "$TRIAL_EVIDENCE"
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 "$TRIAL_GIT" -c core.hooksPath=/dev/null clone --depth 1 --single-branch --branch master --no-tags --no-local "$TRIAL_SOURCE" "$TRIAL_CLONE"
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null "$TRIAL_GIT" -C "$TRIAL_CLONE" remote remove origin
mkdir -p "$TRIAL_CLONE/.scratch/tmp"
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null "$TRIAL_GIT" -C "$TRIAL_CLONE" rev-parse HEAD
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null "$TRIAL_GIT" -C "$TRIAL_CLONE" rev-parse --is-shallow-repository
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null "$TRIAL_GIT" -C "$TRIAL_CLONE" for-each-ref --format='%(refname) %(objectname)'
env GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null "$TRIAL_GIT" -C "$TRIAL_CLONE" remote
```

Freeze HEAD/shallow marker/local refs/config/hook/helpers and absent alternates.
Require only assigned master, no tags/origin, no hardlinked Git objects and no
uncommitted source inputs copied. Keep source current/dirty/history answers,
sibling/common Git storage, host-temp canary and reviewer evidence outside the
clone. Matched unrestricted controls must succeed with identical relevant argv;
reference object IDs/canary bytes remain reviewer-only, not prompts/helper data.

For a tiny trial, prepare its source independently with base task `pending`
plus newline, older H0 historical file, side branch file and H0 tag, current and
dirty nonsecret canaries, and a linked sibling worktree/common Git store.
The [protocol](protocol.md#conditions-and-preparation) specifies these
controls; rebuild them under fresh paths and freeze their new IDs/hashes rather
than reuse private old repositories. No source hook/signing/editor inheritance
is permitted during fixture construction.

## Requested profile and effective runtime review

Start from the retained
[successful TOML](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/runtime.config.toml.txt)
and
[equivalent top-level CLI overrides](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/config-overrides.json).
Replace all old fixture paths with fresh reviewed paths and regenerate hashes;
never execute these historical files unchanged. Required shape:

```toml
model = "gpt-6.1-sol"
model_reasoning_effort = "low"
approval_policy = "never"
default_permissions = "isolation"
web_search = "disabled"
project_doc_max_bytes = 0
allow_login_shell = false

[permissions.isolation]
extends = ":workspace"
[permissions.isolation.filesystem]
":root" = "deny"
":minimal" = "read"
":tmpdir" = "deny"
":slash_tmp" = "deny"
"/usr" = "read"
"/Library/Frameworks/Python.framework/Versions/3.14" = "read"
"/absolute/reviewer/source" = "deny"
"/absolute/reviewer/worktree" = "deny"
"/private/tmp/fresh-reviewer-chosen-name/clone" = "write"
"/private/tmp/fresh-reviewer-chosen-name/clone/.git" = "write"
[permissions.isolation.network]
enabled = false

[shell_environment_policy]
inherit = "none"
[shell_environment_policy.set]
PATH = "/usr/local/Cellar/git/2.55.0/bin:/usr/local/bin:/usr/bin:/bin"
TMPDIR = "/private/tmp/fresh-reviewer-chosen-name/clone/.scratch/tmp"
TMPPREFIX = "/private/tmp/fresh-reviewer-chosen-name/clone/.scratch/tmp/zsh"
GIT_CONFIG_NOSYSTEM = "1"
GIT_CONFIG_GLOBAL = "/dev/null"
GIT_EDITOR = "/usr/bin/false"
GIT_TERMINAL_PROMPT = "0"
```

After adapting the full reviewer-owned TOML, freeze it as
`$TRIAL_EVIDENCE/runtime.config.toml` and record its SHA256. Debug sandbox
selects the profile from the dedicated state's config; install that exact fresh
file, never the user's config:

```sh
test ! -e "$TRIAL_STATE/config.toml"
install -m 600 "$TRIAL_EVIDENCE/runtime.config.toml" "$TRIAL_STATE/config.toml"
```

Require installed/source config bytes and the frozen hash to match before
launch. Actual exec uses `--ignore-user-config`, so the dedicated config file
alone does not supply this condition: it requires the equivalent full top-level
`-c` overrides regenerated from the same reviewed TOML. Gate both
representations and retain their hashes. Do not load inherited user config as a
shortcut.

This abbreviated example must be combined with the full retained tool/skill
settings. Explicit clone `.git` write overrides the workspace Git protection;
without it staging/commit failed. Retain inherited `.codex`/`.agents`
safeguards. Root/source/shared-temp denies remain; do not grant reviewer state
or evidence. Host Codex retains its original TMPDIR for `:tmpdir` expansion.
Child commands receive clone-local TMPDIR and TMPPREFIX. Setting the host
launcher's TMPDIR to clone scratch made the deny target the allowed scratch; do
not do that. TMPDIR alone did not relocate zsh's default `/tmp/zsh` TMPPREFIX.

Full settings disable agents, apps/connectors, plugins/hooks, cloud/bundled
skill catalogs/instructions, browser/computer/web/image tools, JS REPL/tool
search and project rules/documents. Enumerate actual user/system/project
skill-root paths without reading contents, freeze discovered SKILL paths and add
explicit `enabled=false` selectors; discovery skip alone is insufficient. Reject
new paths and inherited MCP servers/legacy sandbox fields. Both turns use strict
config, ignore user config and ignore rules. Managed layers remain applicable;
record nonsecret relevant presence/metadata without dumping user config/auth.

The actual runtime added narrow read access to a different state `tmp/arg0`
helper directory on each CLI invocation. Root independently reviewed this; the
whole state was not granted. Requested config, feature gates and matching debug
sandbox do not prove complete effective tool schema. Review actual turn context
and tool calls; untested parent/managed override conflicts stay unknown.

## Project setup through Make, with fresh offline environments

The complete
[setup report](setup-preparation.md#authorized-launcher-scratch-correction-pending-review)
and
[retained setup runner](audit/retained/ataraxia-isolation-scratch-d388fe8a28bd/scratch-r1/setup-probes.py.txt)
record exact environment/commands and the successful static/focused checks. Use
pinned GNU Make, not macOS `/usr/bin/make` shim, and preserve recursive MAKE.
The locked uv/build-backend pin is 0.12.19. Read `make help` first, then use
Make:

```sh
"$TRIAL_MAKE" -C "$TRIAL_CLONE" help
```

Cache preparation belongs to an independently reviewed host step: a new
dedicated cache populated by the repository's actual `setup`, `verify-setup` and
`verify-check` Make contracts. That approved step may fetch pinned
dependency/hook sources; it copies no existing venv and fetches no project
source. Freeze index condition (`UV_NO_CONFIG=true`, default PyPI), tool
versions and artifact provenance. Prior attempts merely moving wheel directories
did not make the hook resolver succeed; presence is not proof of resolver
metadata/active cache.

Select a new immutable dependency snapshot from the prepared cache. Preserve
complete resolver/index metadata and pinned third-party hook sources; exclude
project editable/build archives, all project Git objects/answers, environment
caches/interpreter/source-path metadata and external links. Enumerate every
file/link/hash and pinned origin/revision. Use filter-on-copy, never mutate raw
cache or rewrite venv paths. Rebuild hook envs through Make. No cache payload is
committed here;
[inventory evidence](audit/retained/ataraxia-isolation-scratch-d388fe8a28bd/dependency-snapshot.json)
records the reviewed selection. A different platform/index/layout is a new
condition, not an automatically equivalent cache.

Put that selected cache inside the fresh clone `.cache`; require `.venv` absent.
Declare the exact Python framework read and clone-local scratch in the profile.
Launch Codex with original host TMPDIR and the freshly installed dedicated
config; select clone-local temp only inside its command. The following focused
launcher follows the retained runner's sanitization and tool/cache conditions.
It is a future reviewer artifact example, not a new production tool or an action
performed by this preservation change. Before approval, adapt the retained setup
plan into `$TRIAL_EVIDENCE/setup-plan.json`, with fresh `root`, selected `base`,
`launcher_tmpdir`, `config_sha256`, `tool_hashes`, `dependency_files` and
`dependency_links`. Freeze the original host TMPDIR value there; do not replace
it with clone scratch. Every dependency entry/link must come from the reviewed
complete resolver/index snapshot and pinned third-party hook source inventory,
not merely a directory containing matching wheel names.

After the specifically approved host launch, use this sanitized environment for
each separately reviewed Make invocation:

```sh
env TRIAL_ROOT="$TRIAL_ROOT" TRIAL_CLONE="$TRIAL_CLONE" TRIAL_STATE="$TRIAL_STATE" TRIAL_EVIDENCE="$TRIAL_EVIDENCE" TRIAL_GIT="$TRIAL_GIT" TRIAL_MAKE="$TRIAL_MAKE" TRIAL_UV="$TRIAL_UV" TRIAL_PYTHON="$TRIAL_PYTHON" "$TRIAL_PYTHON" - <<'PY'
import hashlib, json, os, pathlib, subprocess
trial = {name: pathlib.Path(os.environ['TRIAL_' + name])
         for name in ('ROOT', 'CLONE', 'STATE', 'EVIDENCE', 'GIT', 'MAKE', 'UV', 'PYTHON')}
plan = json.loads((trial['EVIDENCE'] / 'setup-plan.json').read_text())
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
clone = trial['CLONE']
assert str(trial['ROOT']) == plan['root']
assert os.environ.get('TMPDIR') == plan['launcher_tmpdir']
assert not (clone / '.venv').exists()
assert (clone / '.git/refs/heads/master').read_text().strip() == plan['base']
assert sha(trial['STATE'] / 'config.toml') == plan['config_sha256']
assert sha(trial['EVIDENCE'] / 'runtime.config.toml') == plan['config_sha256']
for tool in ('GIT', 'MAKE', 'UV', 'PYTHON'):
    assert sha(trial[tool]) == plan['tool_hashes'][str(trial[tool])]
for path, digest in plan['dependency_files'].items():
    assert sha(clone / '.cache' / path) == digest
for path, target in plan['dependency_links'].items():
    link = clone / '.cache' / path
    assert os.readlink(link) == target
    assert link.resolve().is_relative_to(clone / '.cache')
launch_env = dict(os.environ)
for key in list(launch_env):
    if (key.lower() in ('http_proxy', 'https_proxy', 'all_proxy', 'no_proxy')
        or key.startswith(('GIT_CONFIG_', 'UV_', 'PIP_', 'CODEX_', 'OPENAI_'))
        or key in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'VIRTUAL_ENV',
                   'PYTHONPATH', 'PYTHONHOME', 'MAKE', 'MAKEFLAGS', 'MFLAGS', 'MAKELEVEL')):
        launch_env.pop(key)
launch_env.update(
    CODEX_HOME=str(trial['STATE']), TMPDIR=plan['launcher_tmpdir'],
    GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null',
    GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='credential.helper', GIT_CONFIG_VALUE_0='',
    GIT_TERMINAL_PROMPT='0', GIT_EDITOR='/usr/bin/false',
    UV_OFFLINE='true', UV_NO_CONFIG='true', UV_DEFAULT_INDEX='https://pypi.org/simple',
    UV_PYTHON=str(trial['PYTHON']), UV_PYTHON_DOWNLOADS='never', UV_LINK_MODE='copy',
    UV_CACHE_DIR=str(clone / '.cache/uv'), PREK_HOME=str(clone / '.cache/prek'),
    MAKE=str(trial['MAKE']),
    PATH=str(trial['UV'].parent) + ':' + str(trial['GIT'].parent)
         + ':/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin')
argv = ['/usr/local/bin/codex', 'sandbox', '-P', 'isolation',
        '--include-managed-config', '-C', str(clone), '/usr/bin/env',
        'TMPDIR=' + str(clone / '.scratch/tmp'),
        'TMPPREFIX=' + str(clone / '.scratch/tmp/zsh'),
        str(trial['MAKE']), 'setup', 'UV_OFFLINE=true']
# Keep exact argv/status/output in the new private evidence log, as in retained runner.
result = subprocess.run(argv, env=launch_env, capture_output=True, timeout=300)
assert result.returncode == 0, 'retain failure; no fallback or permission rescue'
PY
```

No source hook/config is inherited: clone construction disables hooks and
system/global Git config, while Make installs only the clone's reviewed pinned
hooks. GNU Make is pinned both as the executable and recursive MAKE. The new
cache must have been built by actual Make hook preparation with the declared
index metadata, then selected without old venvs/editables or external links.
The retained runner is the evidence for the successful batch; this example also
clears inherited Make and host API/config variables and includes the separately
verified TMPPREFIX condition. It does not establish a new execution result.

The fresh-venv guard above applies only to initial setup. Later readiness/check
stages require the newly prepared environment, not an absent venv; preserve the
same pinned launcher environment and retain each stage result without resetting
the destination.

Use the same frozen environment for `verify-setup`, `verify-check` and
`test ARGS=test/unit/test_acceptance_coverage.py`, each separate Make
invocation. The successful deterministic batch passed actual
hooks/lint/format/type/static checks and 16 focused tests. Each setup/check
command was at most five minutes, shared 15 minutes. Prepare a separate fresh
cache-empty destination and run `ci-setup UV_OFFLINE=true`; its expected offline
missing-artifact failure must leave the destination and distinguish cache
failure from permissions/runtime. Do not fall back to network, an old
venv/full-history clone or broader grants. This project readiness evidence is
not a full-project model/resume result.

## Actual executor, auth boundary and UUID checkpoint

Before any model/auth action, root reviews the new plan/config/argv/tool hashes,
skill roots, gates, prompts, helper, hook and matched controls. The gate-only
[archived runner](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/config-gate.py.txt)
checks actual features and initial/resume help parsing without
auth/model/network. Adapt it into a fresh reviewer artifact, freeze its new SHA
and require a new passed record binding the exact fresh plan. No old gate record
may be reused.

Keep CODEX_HOME outside all child roots, new mode 0700, with no old sessions,
config/plugins or auth copied during preparation. Only after specific approved
model launch may the orchestrator stage its existing auth.json into a new
exclusive mode-0600 file; no token output/hashing, auth inspection, login
fallback or unrelated state copying. Model-service transport remains host-owned
and separate from command networking. Do not reuse any prior private
state/credential.

Copy/review adapted
[helper](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/clone-git/neutral-probes.py.txt),
[probe argv](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/clone-git/neutral-probes.json.txt),
[hook](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/clone-git/hooks-pre-commit.txt)
and
[bounded model runner](audit/retained/ataraxia-isolation-tmpprefix-2df60f7109cc/model-trial.py.txt)
into the new fixture/reviewer packet; regenerate every path, canary/control,
reference and hash. Freeze a fresh local-only Git HTTP endpoint/controls if
using the demonstrated network rows. No live remote/auth endpoint is a command
probe. Initial task is pending→ready; resume is ready→verified, target bytes
without newline. Use one initial session and one explicit first UUID resume,
never last, replacement or automatic retry. Both use exact `gpt-6.1-sol` low
effort.

Invoke exact adapted argv equivalent to `codex exec --strict-config
--ignore-user-config --ignore-rules --json -C <clone>` plus all frozen top-level
`-c` overrides and stdin prompt. Resume uses identical exec options, then
`resume <first UUID> -`. Pin Python helper argv; accept only exact command or
vetted shlex-joined shell `-c` wrapper, no compounds/fabrication. Every pre/post
helper requires five allowed controls and 22 denials, including actual variables
and successful zsh heredoc. File denials require explicit permission diagnostic;
Git/network rows require expected diagnostics and matching controls. Unsupported
startup/config/runtime/timeouts/exposure stop, never count as denial.

Accept only the exact startup skip-host-skill warning once per invocation before
turn/tool work; true error, `turn.failed`, changed/late warning or unknown tool
stops. Stream private events early and stop unexpected access/tools. Require
exactly one direct-parent task-only commit per turn, expected bytes, clean
index/tracked worktree, baseline root inventory unchanged except scratch and one
additional hook marker. Root reviews actual initial events/rollout,
model/config/ permission/tool metadata and helper integrity before issuing the
UUID/events/ rollout/plan-bound sentinel. Only then resume. Each turn has 15
minutes; controls and root review share a 30-minute cap. No silent retry or
permission rescue.

## Accepted artifacts and ordinary PR delivery

After final executor correction and independent acceptance, the orchestrator
[explicitly fetches and reconciles approved commits](../artifact-delivery/delivery-protocol.md#bounded-recommendation-and-remaining-acceptance)
into a full-history Work branch, preserving authors/order and implementation/
evidence then cleanup boundaries when that lifecycle is authorized. At unchanged
base IDs can remain; advanced/conflict rebases rewrite IDs and require refreshed
evidence/review. Executor source/auth/history boundaries remain unchanged.

Normal orchestrator-owned PR publication, latest-head CI and maintainer review
follow existing repository contracts. These are downstream responsibility, not
a demand for another live GitHub experiment before this preservation PR. This
current branch already shares the full-history main repository's object store;
it needs no trial import merely to publish its preservation commit. Root owns
commit/publication approval. User requested one preservation commit and no
cleanup yet; keep all incomplete criteria/alternative boundaries explicit.
