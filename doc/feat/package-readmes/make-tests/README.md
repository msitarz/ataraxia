# Make test package documentation

Plan ordered bounded leaves: overview; sandbox/recorder; acceptance/worktree
helpers; integration and executable fixtures. Cover `test/make` and integration,
with fixture descriptions at their nearest owner. Explain real Make/Git/tool
boundaries, process isolation and script-owned registry reuse accurately;
preserve real_tool selection commands and prepared-environment notes.

Follow [parent scope, convention and delivery validation](../README.md).

- **AC-1 TODO** Make test readers can navigate direct contents and distinguish
  reusable sandbox/acceptance/worktree interfaces, fixture responsibilities and
  case-module contracts while retaining operational selection guidance.

  Validation: Merge bounded leaf contracts first; compare helpers/recorders and
  real callers with inventories/diagrams, review existing commands and
  script-owner links, then apply parent delivery checks.
