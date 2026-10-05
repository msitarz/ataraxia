# Preparation allocation

Extract `test_ci_preparation_is_allocated_to_its_consumers` into focused typed
cases using the delivered Make sandbox. Cover ci-setup, ci-test, ci-examples,
setup, ci-package, and ci-check independently. Preserve exact arguments,
preparation-before-consumption ordering, package environment flags, and original
covers provenance. No installs, network calls, new support fixture system, or
execution-case migration. Include the cleaned module in normal strict Pyrefly.

- **AC-1 TODO** Given each preparation target, real Make requests only its
  required preparation and subsequent consumers through fake uv; setup requests
  hooks/build, package requests Python preparation then offline smoke routing,
  and ci-check prepares hooks before checks and audit.

  Validation: run criterion-marked focused cases and strict typecheck; review
  complete observed routing/flags against retained expectations and original
  covers markers, and require latest-head full CI.
