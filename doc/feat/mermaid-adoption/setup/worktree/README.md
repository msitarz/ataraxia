# Check fresh offline worktree rendering manually

Depend on the accepted locked backend setup in the
[setup delivery map](../README.md#delivery-map). The remaining question is
whether a fresh worktree on the prepared local Intel macOS environment can
render SVG offline using existing commands. Accepted backend Linux CI evidence
suffices for Linux; this Work requires no fresh Linux worktree CI run.

`worktree-create` already creates a branch worktree from local `master`, copies
`.cache`, installs locked dependencies offline into a fresh `.venv`, and runs
`verify-setup`. From the prepared source tree, run
`make worktree-create WORKTREE=<new-path> BRANCH=<new-branch>` once with new
disposable selectors; record the actual committed revision it creates. From
inside the new worktree, run the existing forced QuickJS SVG smoke test through
Make:

```sh
make test ARGS=test/script/integration/test_mermaid_backend.py UV_OFFLINE=true UV_NO_SYNC=true
```

The smoke test forces actual rendering with a 30-second timeout and keeps its
diagram files outside the checkout. Creation already checks the environment;
no second `verify-setup` is needed. Remove the disposable worktree manually with
`make worktree-remove WORKTREE=<path>` from the source tree, then delete only
its disposable branch with Git. Preserve caller-owned artifacts and report
failed preparation, rendering or cleanup rather than claiming completion.

This is a manual evidence Work sized for one short review. Add no target,
script, test, `BASE` option, CI route, lifecycle or external-cache machinery;
leave backend selection and shared guidance unchanged. Defining this plan does
not execute or complete the check.

- **AC-1 TODO** Given the prepared local Intel macOS environment, one fresh
  worktree created from default `master` prepares offline and the existing
  backend smoke test successfully forces SVG rendering there offline/no-sync;
  its disposable worktree and branch are then removed.

  Validation: execute the existing creation and smoke-test commands manually,
  then the normal cleanup commands. Retain the actual committed revision,
  offline preparation/render results and cleanup outcome in the execution
  evidence for independent review. Failed or unrun steps leave this criterion
  unresolved; no new inventory or report is required.
