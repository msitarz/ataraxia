# CLI process and complete state

After manifest adaptation, own SelectionProcessResult, tree_state and
run_selection_cli. Use real CLI execution with explicit cwd/PATH/HOME/TMPDIR,
disposable HOME/scratch inside each per-test root but outside observed inputs,
bounded timeout and captured stdout/stderr. Observe all output artifacts and
complete relevant file bytes/link targets without exclusions. Reuse the typed
manifest reader and actual imports; update only needed consumer interfaces,
without CLI case migration, validator cleanup or single-read-double migration.
Follow [parent ownership and sequencing](../README.md).

- **AC-1 TODO** Given fresh accepted or refused inputs, actual CLI observations
  retain precise exit/diagnostics, whole manifests or failure artifacts and
  complete source/destination state; process scratch stays contained outside
  observed inputs and expected answers remain independent of production output.

  Validation: Run marked real-CLI success/refusal and scratch-containment/state
  cases plus existing selection and Make registry consumers; review literal
  artifact expectations and complete snapshots. Precisely include changed
  helpers and owned fixtures/cleaned tests in strict checking; run lint/format,
  doc/ac and latest full CI. Preserve cases/covers and stop/split before
  complete delivery exceeds five-minute review.
