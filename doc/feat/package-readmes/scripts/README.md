# Repository script documentation

Plan ordered bounded leaves: overview/non-registry Python scripts; registry;
shell scripts. Cover actual command entry points, reusable functions/types and
relationships to Make and owning workflow contracts. Preserve commands and
operational constraints; describe shell interfaces by their actual arguments,
environment and effects without copying implementation or inventing APIs.

Follow [parent scope, convention and delivery validation](../README.md).

- **AC-1 TODO** Script readers can locate every direct script and understand
  implemented entry-point/reusable interfaces, shell responsibilities and
  authoritative operational contracts.

  Validation: Merge bounded leaf contracts first; compare Python exports/callers
  and shell invocation sites with module/API summaries, review Make/workflow
  links and preserved commands, then apply parent delivery checks.
