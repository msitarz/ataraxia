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

The planned [lifecycle contract](feat/evaluation-sandboxes/lifecycle/README.md)
extends this private record into a persistent lifecycle marker and adds a
stable OS-held per-name lock with automatic creation/execution/removal
exclusion. Planned cleanup requires explicit owning-orchestrator disposition
after preservation and maintainer review; inactivity alone is insufficient.
These additions are not part of delivered creation. No existing sandboxes
require migration; unsupported old records will be rejected safely.

Preparation is not an isolation boundary. It does not restrict filesystem,
Git-history, network, credentials, references, or model-session access. Use
only under the controls and protocol approved for the intended Evaluation.
The retained preparation evidence supports Darwin Intel conditions only; it
does not establish broader host support, filtered-answer exclusion, model
session isolation, or complete effective-environment capture. A real command
and passing setup checks do not expand those evidence limits.
