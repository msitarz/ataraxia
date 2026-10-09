# Typed dependency arrangements

Own new `compute_dependency_inputs.py` and its strict include. Replace the
duplicated dynamic single_dep class dictionaries with named concrete typed
nodes/runners: B produces1, A receives b and produces b+3. Preserve factory
runner equality and frozen node/hash semantics; no broad callable/class records.
Expose typed arrangements directly rather than itemgetter-based class lookup.

Leave legacy consumers unchanged until their owner adopts this helper. Include
all helper dependencies precisely; do not migrate source or binding
collaborators here or redesign production heterogeneous mappings.

- **AC-1 TODO** Given retained A/B inputs, named precise arrangements preserve
  dependency/factory semantics before consumers without dynamic class
  dictionaries or forward fixture dependencies.

  Validation: inspect signatures/protocol conformance and literal inputs; run
  strict/lint/doc/ac checks and legacy compatibility cases. Consumer leaves
  verify real graph/step behavior, not this declaration alone.
