# Registry selector local evidence

This is mechanical local evidence from branch `work/registry-cache-selection`,
base `b90817aef4464386830e77a25abb3536eee8007b`. Root accepted the exact
preparation record after independent provenance review, then independently
reviewed and accepted the corrected implementation and final 18-test evidence.
AC-1 and AC-2 are verified within the documented reviewed-preparation and tested
condition boundary. Full composed offline validation remains snapshot delivery's
responsibility; no full CI result is claimed.

The demonstration read the original dedicated cache at
`/private/tmp/ataraxia-isolation-online-c44d9fef9c6a/dedicated-cache` without
modification. Actual historical Make setup/readiness/static success and fresh
offline compatibility are retained in the
[setup report](../../../sandbox-isolation/setup-preparation.md#online-result-and-frozen-offline-recreation).
No new online preparation or offline environment recreation ran in this leaf.

The derived preparation record is
`/private/tmp/ataraxia-registry-selection-evidence-r1/preparation.json`, SHA256
`3f89b91636aa14c33d580ae905fb19e4d22ca51455b03201708243b9a3a1b153`. Actual
`make registry-select` with that record, its separately supplied expected digest
and the original cache succeeded into the new destination
`/private/tmp/ataraxia-registry-selection-evidence-r1/result-r4`. It enumerated
2,804 files, 42 links and 42 packages. Result `selection.json` SHA256 is
`774953398001ce1dd8e709fef96e2b58d8f2e59a2e1d9de7c3c66776bae8f88e`. This is a
selection inventory, not a copied cache/environment. Root independently
confirmed the record digest, identical copies of committed corroborating
evidence, matching current declarations, the complete 39-package project lock
boundary, and all selected hashes/link targets against both historical
inventories. Root also confirmed successful actual Make log exits and accepted
this exact record as a bounded trusted preparation input. This acceptance does
not authenticate arbitrary caches or adopt a preparation policy.

Scoped lint, formatting, strict type checking, Markdown checks and `ac-check`
passed; final `ac-test` selected 18 passing tests, including actual Make proxy
integration tests. The focused unit/integration invocation also passed all 18;
the initial pre-review selection passed 15. Ruff's nonblocking size advisory
identified the cohesive package-entry and preparation-validation functions.
Tests cover input immutability, missing/changed entries and declarations,
unsupported conditions, external links, retained failures and destination
guards.

## Enduring derivation from archived evidence

The
[raw preparation evidence](../../../sandbox-isolation/audit/retained/ataraxia-isolation-online-c44d9fef9c6a/)
contains the online plan, raw inventory and successful log. The
[selected offline inventory](../../../sandbox-isolation/audit/retained/ataraxia-isolation-scratch-d388fe8a28bd/dependency-snapshot.json)
records the reviewed successful selection. These committed records are the
sources; the new record duplicates no payloads. The exact reconstruction method
below exposes every selected entry without depending on the new private result:

1. Load `online-plan.json`,
   `online-cache-inventory-09b9619f3b174521b8bbbf288ae955af.json` and the
   selected offline inventory. Retain the online successful JSONL log and all
   three records beside the new record, under their original filenames. The
   record's `evidence` maps each filename to its SHA256. Copying retains
   identical bytes.
2. For every selected inventory link whose path contains `/wheels-v6/pypi/`,
   derive `root` from the prefix, `name` from the next component and `version`
   from the final component before its first hyphen. Its `wheel` is the link
   path; `archive` is `<root>/archive-v0/<target-basename>`; retain its exact
   target. These are the 42 link/package declarations in inventory order.
3. For each package include every selected `files` entry beneath its archive,
   the wheel's `.http` file, and, only for `prek/cache/uv`, the corresponding
   `simple-v25/pypi/<name>.rkyv`. Require each file hash and link target to
   equal the raw inventory. The union is exactly 2,804 files and 42 links. The
   project cache has no generated simple-index records; the hook cache has
   three.
4. Set `trace` to that archive's sole top-level `.dist-info/METADATA` path;
   verify its actual Name/Version during selection. Set `origin` to default
   PyPI, grounded in the reviewed empty-cache, config-disabled Make preparation.
   For each project package, `basis` is
   `uv.lock registry package <name>==<version>`; require this set to equal the
   39 registry packages in the unchanged lock. For hook packages, `basis` is
   `frozen actual pinned hook preparation resolver dependency, outside uv.lock`;
   their exact frozen set is uv 0.12.19, ruamel-yaml 0.19.1, setuptools 84.0.0.
5. Bind `declarations` to the online plan's SHA256 for `uv.lock`,
   `pyproject.toml` and `.pre-commit-config.yaml`; they match the checked-out
   declarations. Bind `condition` to the adapter's exact supported condition.
   `derivation` states the above package/file trace and its trust limits. Root
   reviews the successful log, plan's tool hashes/index condition, declarations
   and this selection boundary before accepting the newly serialized record's
   digest. A reconstructed record may have a different digest from whitespace
   or explanatory text; it requires its own independent acceptance.

The controlled preparation grounds origin, not upstream signatures or lock-wheel
hash authentication of extracted trees. Hashes and METADATA checks preserve
reviewed provenance; they cannot authenticate an arbitrary cache. Complete
opaque resolver records are preserved, never decoded or rewritten.

## Retained failures and remaining validation

The first bounded derivation incorrectly required absent project simple-index
records and stopped; its copied evidence remains at
`/private/tmp/ataraxia-registry-selection-evidence`. The initial selector
counted vendored METADATA and failed; its diagnostic remains in
`/private/tmp/ataraxia-registry-selection-evidence-r1/result/failure.txt`. The
corrected adapter requires top-level package METADATA; successful results are
retained separately at `result-r1`, `result-r2`, `result-r3` and `result-r4`. A
temporary Make `--eval` invocation also failed before preparation on the host's
older Make; the helper subsequently ran through a temporary Makefile. No failed
destination was reset.

Root's consolidated implementation review identified Make variable expansion and
a record double-read. The selector now hashes and parses the same single byte
read; a changing-record regression proves it uses only the accepted bytes.
Changing recipe interpolation to `$(value VAR)` preserved literal argv, but the
first correction's Make proxy still detected automatic command-line export
expansion: 17 tests passed and one failed. The executor stopped and reported
that repeated finding. Root explicitly authorized the established `unexport`
convention for the four new caller inputs. Final proxy tests confirm literal
spaces, apostrophes, dollar expressions and backticks do not execute, and
missing inputs fail before destination creation. Earlier failures remain
recorded here and in the original session/test output.

The final demonstration reran the actual Make target with the original cache,
accepted preparation digest and new `result-r4` destination after both fixes;
its unchanged result hash above binds the corrected selection output. Final
focused lint/type/format, criterion collection/execution and documentation
checks passed; no full CI or composed fresh-environment setup is claimed.

Actual fresh offline setup of the composed registry/hook snapshot remains owned
by [snapshot delivery](../snapshot-delivery/README.md). Passing selection and
historical compatibility evidence do not establish that later outcome.

## Corrective test evidence

The removed contract and this evidence were restored from verified
implementation commit `39a78ac0b9e54b198bbd5d62d01a49aa3980b5dc` for the
separately reviewed test refactor. Production Makefile/selector behavior and the
preparation provenance above are unchanged. Root reviewed and accepted the final
refactor and its inspected mutation evidence; both criteria remain verified
within the original supported boundary. This correction adds no full CI or
composed-setup claim.

The registry target tests now arrange through shared fixtures, perform one
action and assert observed outcomes without process plumbing or body control
flow. An external uv fixture records actual process argv and forwards the real
CLI with `os.execv` when needed. Typed helpers expose exit code, stdout/stderr
and combined diagnostic output. The argument test compares the complete
four-field `RegistryInputs` observation to independent, distinct literal values.
It does not assert the uv prefix, script path or CLI flag order. Missing-input
behavior requires exact Make exit 2, its distinctive diagnostic and no
destination. Normal fixture arrangements copy unchanged artifacts; no permanent
mutation tables, source replacement or environment-selected mutations remain in
tests.

One-time verification copied the actual project configuration, Makefile, CLI and
final test/support/fixture tree into independent temporary project trees. The
fixture's ROOT naturally points to each copied tree. Each mutation changes one
line in that temporary production copy; copied actual `make test` uses the
prepared environment with no sync and offline enabled. The checkout was never
mutated. These exact variants were inspected:

| Temporary production line | Change | Observed result |
| --- | --- | --- |
| Makefile:41 | Replace cache shell-value quoting with bare `$(value CACHE)` | Literal-value test fails: shell error, Make exit 2 instead of 0 |
| Makefile:41 | Swap CACHE/RECORD variable associations, retaining named flags | Literal-value test fails on differing cache/record fields |
| Makefile:41 | Reorder record/cache flag pairs, preserving associations | Named-value test passes |
| Makefile:35 | Comment the four-variable unexport line | No-execution test fails: MAKE_PWNED exists |
| registry_selection.py:266 | Replace parser.error with missing-input stderr output | Missing-input test fails: required diagnostic absent |

Unchanged and restored independent copies each passed all three integration
tests. Each of the four targeted mutants produced exactly one expected failing
test and Make exit 2; the reordered-pair control passed. The final focused and
criterion-selected suite passes 19 tests, superseding the original 18-test
mechanical evidence for these refactored tests. Scoped lint, formatting and
strict helper typing passed.

Inspectable one-time artifacts are retained at
`/private/tmp/ataraxia-registry-refactor-semantic-evidence.md` and
`/private/tmp/ataraxia-registry-refactor-mutations-semantic/matrix.json`; the
latter binds exact original/mutant lines, source line numbers, test names,
commands, expected fragments and full log paths. Normal focused output is at
`/private/tmp/ataraxia-registry-refactor-semantic-tests.txt`. The disposable
verification driver is `/private/tmp/ataraxia-registry-final-mutations.py`, run
through its temporary Makefile. The table and replay method above retain the
behavioral evidence independently of those temporary paths. Earlier refactor
attempts and mutation logs remain retained; no failure artifacts were reset.
