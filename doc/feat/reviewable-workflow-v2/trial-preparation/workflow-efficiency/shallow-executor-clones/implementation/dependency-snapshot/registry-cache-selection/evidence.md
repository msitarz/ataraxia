# Registry selector local evidence

This is mechanical local evidence from branch `work/registry-cache-selection`,
base `b90817aef4464386830e77a25abb3536eee8007b`. Root accepted the exact
preparation record after independent provenance review, then independently
reviewed and accepted the corrected implementation and final 18-test evidence.
That review verified AC-1 and AC-2 within the documented reviewed-preparation
and tested condition boundary. The later unit-test correction below returns both
criteria to TODO until the independent correction review recorded below passed.
Both criteria were then DONE within that same boundary; the CI fixture
correction below returned them to TODO until its independent review passed.
Both criteria are now DONE within the same boundary. Full composed
offline validation remains snapshot delivery's responsibility; no full CI result
is claimed.

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

## Whole-file unit-test corrective evidence

The maintainer explicitly authorized the larger cohesive whole-file review
scope: “lets do the larger review scope, its ok, i authorize it”. This is the
scope exception to the leaf’s five-minute review target, not a production
boundary expansion. Production Makefile, selector, dependencies and integration
tests remain unchanged. The discarded integration Ruff config remains absent.

The final unit file has eight behavior tests, collected as 18 cases. Shared
arrangement uses real files copied from `test/fixtures/registry_selection` into
pytest temporary directories; frozen records, acceptance digests and the whole
expected selection are independent literal data, not production constants or
production-generated expected values. Both registry roots retain opaque resolver
metadata; excluded project/editable/environment fixture entries remain in the
raw cache. Failure cases observe exact exception type, arguments, cause and
unchanged cache bytes/link targets. Four separate actual CLI subprocess cases
observe whole manifest values, recoverable failure, collision preservation and
cache destination rejection with explicit environment, cwd and 30-second
timeout. The single-read case patches only the filesystem `Path.read_bytes`
edge: actual first-read bytes are accepted, a subsequent read would see a
different real file. The helper loads the actual public selector from its
unchanged file; no selector module is patched.

Focused
`make test ARGS='test/unit/test_registry_selection.py test/integration/test_registry_target.py'`
passed 21 cases. Scoped lint and format checks passed. Helper strict typing
passed through a disposable Make target running
`uv run pyrefly check --search-path . test/support.py`; the default project
import root is `src`, so the unmodified `make typecheck ARGS=test/support.py`
could not resolve the script namespace. Passing an option in ARGS correctly
failed the Make path-only guard; no production configuration was changed. These
are local checks, not full CI evidence or a new preparation review.

One-time mutation verification lives outside the checkout at
`/private/tmp/ataraxia-unit-mutations.py`, invoked through
`make -f /private/tmp/ataraxia-unit-checks.mk unit-mutations`. The full matrix
and individual stdout/stderr logs are retained in
`/private/tmp/ataraxia-registry-unit-mutations-final/`. Each independent project
copy contains actual Makefile, selector and final test/fixture tree. It invokes
`make test ARGS=<case>` with the already prepared environment,
`UV_NO_SYNC=true`, `UV_OFFLINE=true` and `UV_PYTHON_DOWNLOADS=never`. Only one
copied production line changes per mutant; no checkout source or normal fixture
chooses a mutant. All 18 mutated cases exited with Make status 2 and the reasons
below. Normal and restored independent copies exited 0 with all 21 focused cases
passing. The following exact line replacements and selected cases make the check
replayable without retaining a mutation framework in normal tests.

- `test_selector_returns_only_reviewed_inputs_without_changing_cache`: copied
  selector line 249; replace
  `return Selection(files, links, declared, expected)` with
  `return Selection({}, links, declared, expected)`. Observed failure:
  `Differing attributes`.
- `test_selector_rejects_changed_inputs_without_modifying_cache[missing-payload]`:
  copied selector line 90; replace
  `if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):`
  with `if False:`. Observed failure: `FileNotFoundError`.
- `test_selector_rejects_changed_inputs_without_modifying_cache[external-link]`:
  copied selector line 245; replace
  `if link.readlink().as_posix() != target or not link.resolve().is_relative_to(`
  with `if False and not link.resolve().is_relative_to(`. Observed failure:
  `DID NOT RAISE`.
- `test_selector_rejects_changed_inputs_without_modifying_cache[changed-declaration]`:
  copied selector line 223; replace
  `if digest(regular(repository, name)) != sha:` with `if False:`. Observed
  failure: `DID NOT RAISE`.
- `test_selector_rejects_changed_inputs_without_modifying_cache[changed-evidence]`:
  copied selector line 229; replace
  `if digest(regular(record.parent, name)) != sha:` with `if False:`. Observed
  failure: `DID NOT RAISE`.
- `test_selector_rejects_changed_inputs_without_modifying_cache[unapproved-record]`:
  copied selector line 213; replace
  `or hashlib.sha256(record_bytes).hexdigest() != expected` with `or False`.
  Observed failure: `KeyError: 'condition'`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[unsupported-uv]`:
  copied selector line 217; replace
  `if strings(data["condition"]) != CONDITION:` with `if False:`. Observed
  failure: `DID NOT RAISE`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[unsupported-index]`:
  copied selector line 217; replace
  `if strings(data["condition"]) != CONDITION:` with `if False:`. Observed
  failure: `DID NOT RAISE`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[unsupported-platform]`:
  copied selector line 217; replace
  `if strings(data["condition"]) != CONDITION:` with `if False:`. Observed
  failure: `DID NOT RAISE`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[unsupported-layout]`:
  copied selector line 217; replace
  `if strings(data["condition"]) != CONDITION:` with `if False:`. Observed
  failure: `DID NOT RAISE`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[missing-metadata]`:
  copied selector line 177; replace
  `if not payload or not metadata <= files.keys():` with `if False:`. Observed
  failure: `inventory contains undeclared entries`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[undeclared-artifact]`:
  copied selector line 236; replace
  `if allowed != files.keys() or {p.wheel for p in declared} != links.keys():`
  with `if False:`. Observed failure: `DID NOT RAISE`.
- `test_selector_rejects_unsupported_records_without_modifying_cache[declared-version-mismatch]`:
  copied selector line 167; replace
  `if not wheel.startswith(f"{root}/wheels-v6/pypi/{name}/{version}-"):` with
  `if False:`. Observed failure: `payload METADATA contradicts preparation`.
- `test_selector_uses_only_the_single_accepted_record_read`: copied selector
  line 216; replace `data = mapping(json.loads(record_bytes))` with
  `data = mapping(json.loads(record.read_bytes()))`. Observed failure:
  `KeyError: 'condition'`.
- `test_cli_delivers_the_reviewed_manifest_without_changing_cache`: copied
  selector line 280; replace `"links": result.links,` with `"links": {},`.
  Observed failure: `Differing attributes`.
- `test_cli_retains_missing_record_failure_without_changing_cache`: copied
  selector line 291; replace
  `(destination / "failure.txt").write_text(message + "\n")` with
  `sys.stderr.write(message + "\n")`. Observed failure:
  `assert None is not None`.
- `test_cli_preserves_an_existing_destination`: copied selector line 272;
  replace `destination.mkdir(parents=True, exist_ok=False)` with
  `destination.mkdir(parents=True, exist_ok=True)`. Observed failure:
  `assert 0 == 1`.
- `test_cli_rejects_destinations_inside_the_input_cache`: copied selector line
  268; replace
  `if destination.resolve().is_relative_to(Path(args.cache).resolve()):` with
  `if False:`. Observed failure: `assert 0 == 1`.

The first completed unit mutation matrix remains separately at
`/private/tmp/ataraxia-registry-unit-mutations/matrix.json`. A broader fixture
format check then failed because the declaration fixture was plain text in a
TOML file. Declaration fixture content became a valid comment; the static
records and independent expected acceptance digest were refreshed. Final
normal/restored 21-case runs and every one of the 18 mutation rows passed
the same verification again against that final data. The external one-time
fixture construction method is retained at
`/private/tmp/build-registry-unit-fixtures.py`; it imports no production
selector or constants and is not used by normal tests. Earlier runtime
namespace-import and default helper typing failures remain development
limitations resolved by loading the unchanged script and the explicit typing
search path, respectively.

Final focused command output and exit statuses are retained in
`/private/tmp/ataraxia-registry-unit-checks/results.json` and its numbered
logs. The full mutation matrix includes each case, exact original/mutant
line, source line number, command, exit and observed reason. No mutation
selection environment variable or production replacement mechanism remains
in normal fixture code. Independent review of this refreshed unit evidence
was pending at that stage and passed after the consolidated corrections below.

## Consolidated unit review corrections

The missing-record CLI case now checks the actual missing record path,
filesystem reason and recovery instruction in the retained `failure.txt` text
itself. It checks that text equals stderr, names the missing path in stderr, and
observes the whole destination inventory containing only that exact diagnostic
file. Manifest observation now rejects a missing or extra top-level key with
`ValueError("selection manifest must contain exactly the five public fields")`
before comparing the documented fields; it no longer silently projects extras
away.

An ordinary `from script.registry_selection import Package, Selection, select`
was tested in a disposable project copy through the default Make test target.
It failed before collection with `ModuleNotFoundError: No module named 'script'`
under pytest's src-only path and importlib mode; the probe output is retained
at `/private/tmp/ataraxia-registry-import-probe.txt`. The loader therefore
remains, loading the unchanged public script by its actual copied location.
Helper typing now uses the standard target: `PYTHONPATH=. make typecheck
ARGS=test/support.py`, which passed strict checking with zero errors. This
explicit import path replaces the disposable typing target, without suppressing
diagnostics or changing production configuration. Pyrefly reports the explicit
PYTHONPATH in its warning; other environments need that same scoped path.

Final corrected focused and criterion-selected tests each passed all 21 cases;
scoped lint, formatting and standard helper typing passed. Full command output
is retained at `/private/tmp/ataraxia-registry-unit-checks-reviewed/`. The
repeated matrix at `/private/tmp/ataraxia-registry-unit-mutations-reviewed/`
contains all original 18 case mutations plus the three additions below. All
21 mutants failed with intended reasons and Make exit 2; normal/restored
copies each passed all 21 tests. Original matrices and logs remain intact.

- `extra-manifest-key`:
  `test_cli_delivers_the_reviewed_manifest_without_changing_cache`; replace
  copied selector line 283 `"condition": CONDITION,` with
  `"condition": CONDITION, "unexpected": "extra",`. Expected and observed
  failure:
  `ValueError: selection manifest must contain exactly the five public fields`.
- `unrelated-failure`:
  `test_cli_retains_missing_record_failure_without_changing_cache`; replace
  copied selector line 291
  `(destination / "failure.txt").write_text(message + "\n")` with
  `(destination / "failure.txt").write_text("unrelated\n")`. Expected and
  observed failure: `in 'unrelated\n'`.
- `extra-failure-file`:
  `test_cli_retains_missing_record_failure_without_changing_cache`; replace
  copied selector line 291
  `(destination / "failure.txt").write_text(message + "\n")` with
  `(destination / "failure.txt").write_text(message + "\n"); (destination / "extra.txt").write_text("extra")`.
  Expected and observed failure: `extra.txt`.

All 28 fixture entries are now explicitly staged under the requested fixture
directory, including both internal wheel symlinks, the setup log, hidden
pre-commit declaration, uv.lock and editable wheel contamination. No ignore
rule excludes these entries. `git checkout-index` reproduced those staged
entries at `/private/tmp/ataraxia-registry-fixture-tracked/`; every file's bytes
and each symlink target matched the local fixture. A disposable project using
only those reproduced fixture entries passed all 21 focused tests. The exact
path inventory, symlinks, command and exit are retained in
`/private/tmp/ataraxia-registry-tracked-replay.json`, with full output in its
`.txt` sibling. No commit or publication occurred during this preparation.

Root independently reviewed the corrected assertions and manifest helper,
verified all 23 matrix logs and their expected fragments and exits (21 mutants
plus normal/restored copies), and independently verified the literal fixture
digests, selected files, links, declarations, evidence and expected inventory.
Root confirmed no production or accepted integration changes and accepted the
corrected artifact. At that review, AC-1 and AC-2 were DONE within the original
reviewed preparation and tested-condition boundary. The authorized larger review
scope exception remains recorded above; this review claims neither full CI nor
composed offline validation.

## CI-discovered nested prek fixture correction

[CI run 37219012745](https://github.com/msitarz/ataraxia/actions/runs/37219012745)
failed the Check job during actual `prek prepare-hooks` and failed
`test_prek_passes_message_filename` in the Test job at published head
`d100f1f`. Prek discovers the nested fixture
`test/fixtures/registry_selection/common/repository/.pre-commit-config.yaml`;
its comment-only content parsed as no configuration, producing
`unexpected end of input`. A YAML syntax check alone had not exercised prek's
configuration contract. Full failed job output is retained at
`/private/tmp/ataraxia-registry-ci-37219012745-failed.txt`. The previous unit
review and passing local reports above are historical; this new CI finding
invalidated their fixture compatibility evidence. Both criteria returned to
TODO until the independent acceptance below.

Only that fixture now contains the exact UTF-8 bytes
`# frozen fixture declaration\nrepos: []\n`. Its SHA256 is
`1ea9cebfe015605bc41386b69a4431c65cb3cf1bd84701173a6b12a98da10262`. Each of the
eight literal records has that declaration hash; their separately frozen
acceptance digests were recomputed from their exact bytes. The whole expected
manifest's preparation SHA is now the accepted fixture record hash
`86a0bd7e2b6004ca8deaaf776b1f344fa65b1531ccf3585a423635d14f559cff`. The one-time
method at `/private/tmp/registry-ci-fixture-fix.py` writes the exact fixture
bytes, hashes them with standard SHA256, updates the declaration in each static
JSON record, serializes with indent 2 and trailing newline, hashes those bytes,
and updates `digests.json` and only the expected manifest's preparation SHA. It
imports no selector, constants or production digest helper. This changes no real
preparation record, payload inventory, source, tests or production
configuration.

Actual `make verify-setup` passed offline and reported no environment changes.
Actual `make ci-check-setup UV_OFFLINE=true` passed locked synchronization and
`uv run --no-sync prek prepare-hooks`, exercising nested discovery without
network fallback. Focused registry tests plus
`test/integration/test_commit_message.py::test_prek_passes_message_filename`
passed all 22 cases. `ac-test` passed all 21 registry cases. Scoped lint,
formatting, standard helper typing with `PYTHONPATH=.`, `ac-check` and
documentation checks passed. Full outputs and exact commands are retained
in `/private/tmp/ataraxia-registry-unit-checks-ci-fixed/`. No new full CI result
is claimed; the latest failed CI remains authoritative until republished CI
passes.

The repeated disposable matrix at
`/private/tmp/ataraxia-registry-unit-mutations-ci-fixed/` ran against the final
fixture bytes: all 21 copied-production mutants failed with their intended
fragments and Make exit 2; unmodified and restored copies each passed all 21
registry tests. The prior matrix logs remain intact. The fixture directory is
explicitly staged. All 28 indexed fixture entries, including the valid nested
configuration and both symlinks, were reproduced with `git checkout-index` under
`/private/tmp/ataraxia-registry-fixture-tracked-ci-fixed/`; their bytes and link
targets matched. The disposable project using those reproduced entries passed
all 21 registry tests, with exact path inventory, symlinks, command and exit
retained in `/private/tmp/ataraxia-registry-tracked-replay-ci-fixed.json` and
full output in its `.txt` sibling. Production and accepted test files remain
unchanged. No commit or publication occurred during this correction. The
previously authorized larger cohesive review scope still applies.

Root independently reviewed the exact `repos: []` addition and required hash
updates, recomputed the final configuration hash, all eight record digests and
the expected manifest digest, and inspected all 23 matrix logs for expected
fragments and exits. Root also inspected the actual `verify-setup`, offline
`ci-check-setup`, focused 22-test and selected 21-test output. Root accepted the
corrected fixture compatibility and refreshed evidence; AC-1 and AC-2 are now
DONE within the unchanged reviewed-preparation and tested-condition boundary.
The failed CI run remains historical evidence; CI for a subsequently published
correction is still pending, and no full CI success is claimed.
