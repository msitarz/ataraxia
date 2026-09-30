# Documentation checks

Investigate existing tools before writing custom rules. Adopt deterministic
checks behind `make doc-check` only after their behavior fits this repository.
Keep tool choices and integration separately reviewable.

## Works

- **DONE** Tool investigation — selected rumdl 0.2.78 for Markdown formatting
  and offline link checks; deferred other tools.
- **TODO** [Checker integration](checker-integration/README.md)
- **TODO** [Acceptance traceability](acceptance-traceability/README.md)
