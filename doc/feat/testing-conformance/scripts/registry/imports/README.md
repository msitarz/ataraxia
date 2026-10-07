# Actual registry imports

Use the actual supported registry module and its precise public types/functions
in script-owned support. Replace dynamic import/type aliases without
process-global sys.path rewriting or duplicate model identities. Normal-check
the changed typed helper; no fixture migration or API change. Stop and split if
strict inclusion needs unrelated helper repair. Follow
[parent ownership, sequencing and checks](../README.md).

- **AC-1 TODO** Given actual registry imports, existing helper consumers receive
  the real public types/functions with stable selector and validator outcomes.

  Validation: Run registry unit/process cases and Make registry consumers;
  review runtime type identity and precise checked signatures; run strict
  typing, lint/format, doc/ac checks and latest CI.
