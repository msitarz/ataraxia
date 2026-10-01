# Validation policy

Read this file when choosing checks or reporting validation evidence. The
[Makefile](../Makefile) owns the available commands and their behavior.

While preparing a draft PR, run the checks affected by the change, including
focused tests for code changes. A local full `make ci` run is optional; it is
not a prerequisite for opening every draft PR. Report relevant failures,
pending checks, reused evidence, and checks not run accurately.

Before merge, require the full CI workflow to pass on the latest reviewed PR
head. A result from an earlier revision does not cover later changes. The
[CI workflow](../.github/workflows/ci.yml) owns its jobs and required commands.
Local focused checks do not replace this merge gate.

Run `make ci` when a full local run is useful:

```sh
make ci
```

Full `make ci` runs local verification before the required network-dependent
audit. An audit failure still fails CI, while completed local results remain
available. The CI check job also runs its local checks before auditing.

After setup, agents without network access can run `make verify` for local
evidence. It checks the locked environment without installing or resolving
dependencies, then reuses the same local check recipes as CI with uv network
access disabled. Missing or stale environments fail; rerun `make setup` with
network access to prepare them. A passing verification does not include the
vulnerability audit and cannot satisfy the full CI merge gate. Report an audit
as unrun or failed, and report any checks that could not run.

CI rejects a missing or stale `uv.lock` with `uv sync --locked`. Subsequent
checks use the synchronized environment without updating dependency resolution.
After intentional dependency changes, run `uv lock` and commit the updated
lockfile. The YAML, conflict-marker, and private-key checks reuse the pinned
hooks in `.pre-commit-config.yaml` and inspect all tracked files.

For a manual example run, use:

```sh
uv run ataraxia --sink example/crossover.py --shards-dir sample --output results.json
```

`make ci-package` builds a wheel, installs it into a temporary isolated virtual
environment, and runs the copied sample strategy and shards outside the
checkout. It checks the installed console entry point, printed totals, and JSON
accounts. The temporary environment and artifacts are removed when the check
finishes.
