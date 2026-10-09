# Generate literal registry arguments through actual Make

After adoption, own one precisely typed property in
`test/make/integration/test_registry_target.py`. Reuse script-owned
`copy_registry_project`, `registry_case`, `RegistryCase` and
`run_registry_target` from `test/script/registry_transport.py` without changing
their interfaces or the existing hostile examples/refusal tests/fixtures.
Assemble a new case using the existing explicit environment and four
independently generated assignments; the harness supplies actual Make, fake
external uv and a 30-second timeout.

Each example gets a fresh temporary context containing its own project and
process HOME/TMPDIR directories, with no inherited Make flags or shared logs.
Generate four nonempty values, each with a distinct ordinary prefix and bounded
0 through 64 ASCII-character tails drawn from letters/digits, spaces, quotes,
dollar signs, parentheses, backticks, semicolons, ampersands, pipes,
backslashes, hashes, equals signs and glob characters. Exclude NUL/newlines and
ambiguous standalone CLI flag values. Explicit examples include the existing
Make/shell/ backtick payloads targeting `MAKE_PWNED`, `SHELL_PWNED`,
`TICK_PWNED`, each alone and combined with quoting/spaces. Keep the immutable
named examples intact.

Use 25 examples and only the subprocess deadline override. Assert exit zero,
the complete four literal `RegistryInputs` equal to generated inputs and no
execution markers; do not reconstruct shell quoting or assert a copied escaping
algorithm. Preserve external-log validation and precisely typed harness results.
No production/tool/helper API changes or fixture-health suppression.

- **AC-1 DONE** Given four bounded hostile literal values and an isolated fresh
  arrangement per example, real `registry-select` transports every value exactly
  through fake external uv without executing caller expressions, while named
  transport/refusal coverage and strict folder typing remain intact.

  Validation: review independent values/payloads, complete comparisons and
  per-example isolation; run generated and all three named registry-target cases
  through Make, inspect strict-folder results/timeouts/settings, then doc/ac
  checks. Report observed results without performance claims.
