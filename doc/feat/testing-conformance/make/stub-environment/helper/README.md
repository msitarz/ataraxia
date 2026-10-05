# Shared fake-uv helper

Add a typed process helper and real fixture-file recorder with explicit
child environment, minimum copied Make dependencies, argument/environment
logs, configurable command failure, captured output, and timeout. Add small
real-Make smoke cases proving the helper; do not migrate existing routing yet.
Reuse script-owned registry arrangements narrowly instead of modifying them.

- **AC-1 TODO** Given fresh temporary arrangements, real Make launches the
  recorder, preserves arguments/flags, and exposes configured failure and
  diagnostics.

  Validation: run focused criterion-marked cases and strict typecheck; review
  precise helper/fixture inclusion, preserved covers markers, and full CI.
