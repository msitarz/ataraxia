# Minimal restart observations

The deterministic restart on 2026-10-03 initially failed at sandbox startup.
After review and specific host-side execution approval, the orchestrator ran
the same child commands/profile: clone write succeeded and source-canary read
was denied. This demonstrates only the minimal standalone filesystem boundary;
neither candidate is qualified and AC-1/AC-2 remain unresolved. No model
inference ran.

## Frozen fixture and commands

Tool cwd was `/private/tmp/ataraxia-shallow-isolation`. The new disposable root
was `/private/tmp/ataraxia-isolation-restart-71ca4e8451c3`; the interrupted
first fixture was left untouched. Before execution, `evidence/frozen-plan.json`
recorded explicit commands, 30-second timeouts, environment, stop handling and
profile hash. Its sibling `config.toml` preserves the requested profile.
Construction and probe JSON logs remain under this new root's `evidence`,
outside the clone and requested readable executor paths.

Construction used `GIT_CONFIG_NOSYSTEM=1`, `GIT_CONFIG_GLOBAL=/dev/null`,
`GIT_EDITOR=/usr/bin/false`, `GIT_TERMINAL_PROMPT=0`, explicit fixture identity,
disabled commit/tag signing, and an empty dedicated hooks directory. The five
separate Git operations (init, add, explicit-message commit, shallow clone and
remote removal) exited zero without interaction. The frozen current-tree
commit is `9ecc52b`; the clone used `--no-local --depth=1 --single-branch
--no-tags --branch=master`. Historical fixture construction was unnecessary
for this minimal stage and was not performed.

The requested profile used `extends = ":workspace"`, denied `:root`, `:tmpdir`,
`:slash_tmp` and the disposable source, allowed `:minimal` reads and clone
writes, disabled command networking, and set `approval_policy = "never"`.
The harness used a fresh `CODEX_HOME` containing only this profile. Profile
configuration was frozen. The initial launch failed; the approved host-side
launch later established the two recorded command outcomes, without a complete
effective-state inventory. Earlier read-only help inspection recorded
CLI 0.159.3; no version/platform reinspection was performed in this restart.

## Actual results

At 20:46:43 UTC, `/bin/cat` of the disposable source's `current.txt` exited
zero. Its output matched the frozen non-secret canary hash; contents were not
printed or passed to a model. The JSON control record retains the hash and match
result.

The allowed-write probe invoked the following exact argv, with the frozen
fresh-state environment:

```text
/usr/local/bin/codex sandbox -P isolation --include-managed-config
  -C /private/tmp/ataraxia-isolation-restart-71ca4e8451c3/clone
  /bin/sh -c 'printf ready > /private/tmp/ataraxia-isolation-restart-71ca4e8451c3/clone/task.txt'
```

At 20:46:43 UTC it exited **71**, with empty stdout and stderr:

```text
sandbox-exec: sandbox_apply: Operation not permitted
```

The harness observed `task.txt` still containing `pending`. This is an
unsupported execution boundary in the current permission context, not evidence
of successful file denial. Its underlying cause was not investigated. No
escalation, retry, weakened profile, alternative execution route or cleanup was
attempted during this initial invocation. Both subprocesses completed within
their 30-second limits. Its exit-71 record is retained unchanged.

## Interpretation and remaining work

The approved standalone launch establishes an allowed clone file write and a
denied current-source read under the unchanged child profile. The successful
control and fresh source hash distinguish denial from a missing fixture. This
supports a launch-context explanation for the prior failure; the exact syscall
cause was not diagnosed. Candidate B still requires broader checks and model
work; candidate A remains untested. Historical objects/fetches, symlinks,
alternate tools/roots, indirect exposure, networking, setup, hooks/commits,
conflict handling and same-session correction remain unrun. No performance or
cost conclusion follows. The first preparation failure and exit-71 observation
remain part of the evidence.

## Approved standalone launch

The user authorized investigating a supported launch context. A disposable
runner is retained at the original restart root's
`evidence/standalone-probes.py`. Its reviewed SHA256 is:

```text
6ee3c1146ba656c1f7164c47d6b8aa9ff690fecbb34a827912f3ea95726d7fb7
```

After independent file review, the orchestrator executed the following with
specifically approved `require_escalated` host-side launch from the existing
worktree cwd. This approval applied to the launcher; child restrictions stayed
unchanged:

```text
python3 /private/tmp/ataraxia-isolation-restart-71ca4e8451c3/evidence/standalone-probes.py
```

The runner exited zero. The executor read the orchestrator-owned record at
`evidence/external-launch-e53b7bc632954affa2c8c0f4fd1e4269.jsonl` under the
restart root. At 20:57:18 UTC, manifest/config/source hashes passed and the task
was still pending. At 20:57:19 UTC, write exited zero with `ready` observed;
source read exited one with empty stdout and this child-command diagnostic:

```text
cat: /private/tmp/ataraxia-isolation-restart-71ca4e8451c3/source/current.txt: Operation not permitted
```

The runner verifies the frozen manifest and both config hashes, checks the
original source-control hash, and requires `task.txt` still equal to `pending`.
It executes only the existing write argv and, only if that command exits zero
and actually writes `ready`, the existing source-read argv. Each has a
30-second timeout. Child argv/profile/state are unchanged; no bypass flags,
model calls, network setup, Git operations, unsandboxed fixture writes,
configuration changes or process cleanup are included.

It writes distinct exclusive-create `external-launch-<id>.jsonl` records,
preserving every previous log including exit 71. Output hashes and byte counts
record potential exposure without printing canary contents. A denial result
requires a failing `cat` diagnostic naming the canary path, no stdout, and no
sandbox-launch error; launch failure remains inconclusive. These observed
outcomes establish only this minimal standalone command boundary, not
custom-agent or resumed-session enforcement. Further host-side launches require
orchestrator execution approval; no blanket bypass authority follows.
