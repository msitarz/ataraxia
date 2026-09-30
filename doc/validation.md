# Validation policy

Read this file when choosing checks or reporting validation evidence. The
[Makefile](../Makefile) owns the available commands and their behavior.

For code changes, run focused tests during development. Before pushing a branch
or opening a PR, run all CI checks locally, including for an early draft PR
containing only a specification:

```sh
make ci
```

Full `make ci` runs local verification before the required network-dependent
audit. An audit failure still fails CI, while completed local results remain
available. The CI check job also runs its local checks before auditing.

After setup, agents without network access must run `make verify` when `make ci`
cannot run. It checks the locked environment without installing or resolving
dependencies, then reuses the same local check recipes as CI with uv network
access disabled. Missing or stale environments fail; rerun `make setup` with
network access to prepare them. A passing verification does not include a
vulnerability audit. Report the audit separately as unrun or failed, and report
any checks that could not run.

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
environment, and runs the copied sample strategy and shards outside the checkout.
It checks the installed console entry point, printed totals, and JSON accounts.
The temporary environment and artifacts are removed when the check finishes.
