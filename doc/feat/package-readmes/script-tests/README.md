# Recent script test package documentation

Plan ordered bounded leaves: overview; remaining helpers/fixtures; unit and
integration inventories. Cover `test/script`, its unit/integration namespaces
and nearest fixture ownership. Document canonical imports, actual process
boundaries and shared Make reuse. The registry-selector inputs, records,
manifest/process/transport helpers and selection/digest/provenance notes in the
reviewed baseline were retired by the
[selector cleanup](../../reviewable-workflow-v2/trial-preparation/workflow-efficiency/shallow-executor-clones/registry-selector-cleanup/README.md);
exclude them from this package documentation plan. Keep shared support edits
serial and reusable API inventories distinct from case-module summaries.

Follow [parent scope, convention and delivery validation](../README.md).

- **AC-1 TODO** Script test package readers can find each direct
  module/subpackage and understand reusable input, observation, transport and
  fixture contracts plus the behaviors owned by unit/integration case modules.

  Validation: Before execution, merge bounded leaf contracts for these slices.
  Review helpers/fixtures and callers, full direct inventories,
  architecture/navigation and preserved notes under parent delivery checks.
