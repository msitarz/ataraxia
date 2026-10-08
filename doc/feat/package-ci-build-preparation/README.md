# Prepare installed-package CI builds

The installed-wheel job in PR #172 can fail after a uv_build bump: current
`ci-package-setup` prepares Python, then `verify-package` builds offline without
the new backend cached. Prepare wheel/backend requirements while CI preparation
can use the network, preserving the offline installed-wheel smoke boundary.

- **TODO** [Build preparation fix](fix/README.md): Make routing/regressions and
  real cold-cache installed-wheel validation.

Independently review these temporary ad hoc contracts before implementation;
carry their verified delivery and cleanup in the single fix PR. This is one
responsibility with a five-minute complete-diff review target; no expanded
multi-PR plan, dependency bump or change to PR #172 is authorized. Resume the
separate source-forwarding Work afterward.

- **AC-1 TODO** Given an initially empty package-build cache, installed-package
  CI prepares its declared backend before offline verification and successfully
  smoke-tests the installed wheel, without weakening offline/no-sync checking.

  Validation: independently review the child change, focused Make evidence and
  real cold-cache runs, including temporary uv_build 0.12.23 validation; require
  latest-head full CI before merge.
