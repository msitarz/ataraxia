# Payload metadata and declared inventory

After inventory, clean metadata/local-source/environment and selected-inventory
cases with their remaining owned fixtures. Preserve name/version contradictions,
required file/link inventories and undeclared entries. Remove legacy
validation/support/conftest pieces only when no callers remain; retain unrelated
fixtures. Follow [parent ownership, sequencing and checks](../README.md).

- **AC-1 DONE** Given literal metadata and selected inventories, supported
  values pass while conflicting, local/environment or missing/extra entries fail
  with precise errors/causes.

  Validation: Run marked metadata/inventory cases and complete registry/Make
  consumer suites; review preserved counts/covers, strict inclusion and safe
  legacy removal; lint/format, doc/ac and latest CI.
