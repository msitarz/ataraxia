# Real module loading outcomes

After valid arrangements, own `unit/test_util.py` and `integration/test_util.py`
and their strict includes. Preserve `test_import_file_raise`'s missing path
`i do not exist` (no extension), under disposable state: ModuleError reason
`Cannot load module`, with no invented FileNotFoundError contract. Preserve
`test_import_file` through copied `import_bar.py`, invoking the loaded callable
and comparing the complete literal Bar with all fields 1 rather than only close.

Validate dynamic module attributes/results at the import boundary before
exposing precise test values; do not hide ModuleType/production typing with
casts, ignores or unrestricted mocks. Keep filesystem/module execution real and
input files under tmp_path. Do not redesign import_file or add unrelated loader
policy.

- **AC-1 DONE** Given the retained missing and loadable modules, real
  import_file produces the exact failure or complete independent callable result
  with precise checked tests and copied named source.

  Validation: inspect the preserved missing-path semantics and loaded-value
  adaptation; run both modules and the subtree's required checks.
