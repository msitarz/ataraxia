# Managed evaluation sandboxes

Read when creating or using a managed evaluation sandbox. The command prepares
a trusted, online workspace; it does not enforce execution isolation or
authorize a model run.

Create a sandbox with:

```sh
make sandbox-create NAME=trial-a
```

The default root is `<system temp>/<project name>/sandboxes`, where the
project name comes from `pyproject.toml`. An absolute `SANDBOX_ROOT=/path`
selects another managed root. `NAME` is 1–64 ASCII letters, digits, dots,
underscores, or hyphens and must start with a letter or digit.
The generated branch is `work/sandbox-<NAME>`, so the value must also satisfy
Git's ref-name rules; for example, `bad..name` is rejected because Git forbids
consecutive dots in a ref.

Creation freezes the current local `master` commit, then makes an independent
depth-one clone with branch `work/sandbox-<NAME>`. Uncommitted source files are
not included. At the final location it runs online `make setup`, which installs
the locked development environment and pinned hooks, followed by
`make verify-setup`.

The root-private `.<NAME>.ataraxia-sandbox.json` record identifies the source
Git common directory, project, selected base, and preparation state. If clone,
setup, or readiness fails, the partial sandbox and failure diagnostics remain;
the name cannot be retried or overwritten. Inspect the state record and partial
workspace before deciding how to recover.

## Delivered lifecycle safety

The shared lifecycle foundation extends this record with a versioned private
identity marker, fresh generation, stable per-name OS lock and create
integration. Lock probes do not mutate persistent state, and unsafe or
inconsistent observations are unknown.

The delivered execution lifecycle binds attempts to the source Work, owning
orchestrator, generation and native workspace identity. It retains prior
attempts and private artifact paths; a session UUID is recorded only when
observed. Uncertain process lifetime stays unknown and blocks another attempt.
Recovery requires trusted host evidence tied to the same run, generation,
workspace and retained artifact directory. Lock release after wrapper death,
parent-PID exit or process-group signaling alone does not prove descendants
stopped. This is a shared attempt and recovery protocol, not a native
containment backend; the native execution consumer must supply a supervisor
with explained platform limits. Reviewed cleanup disposition after
preservation and maintainer review remains planned in the
[lifecycle contract](feat/evaluation-sandboxes/lifecycle/README.md). No existing
sandboxes require migration; unsupported old records are rejected safely.

Preparation is trusted host work, not an isolation boundary. Root-private file
modes do not isolate same-UID preparation commands; enforced native execution
must deny sandboxed child access to private control paths. Preparation does not
restrict filesystem, Git-history, network, credentials, references, or
model-session access. Use only under the controls and protocol approved for the
intended Evaluation.
The retained preparation evidence supports Darwin Intel conditions only; it
does not establish broader host support, filtered-answer exclusion, model
session isolation, or complete effective-environment capture. A real command
and passing setup checks do not expand those evidence limits.
