# Complexipy 8.0.1 findings

Assessed 2026-10-17 at repository revision
`ef1f6eea938b60b9a98e3c544ae1a9582ba22276` on branch
`work/complexipy-investigation`. Latest stable at execution start was
complexipy 8.0.1: PyPI says released 2026-09-07; the changelog and release note
date it 2026-09-06. No older release was executed or compared.

## Documented claims and release evidence

| Area | Current official documentation | 8.0.1 source or observed behavior |
| --- | --- | --- |
| Scoring | The score guide says each `and`/`or` adds a point, `match` adds none, and `else` adds none. | `count_bool_ops` counts Boolean AST nodes; `Match` adds one point plus nesting; each `elif`/`else` clause adds one. Match-case guards are not visited. A six-operand same-operator `if` scored 2; an `if`/`elif`/`else` chain scored 4; a `match` with a Boolean guard scored 1. |
| CLI and configuration | Native Rust CLI; default threshold 15; CLI, `complexipy.toml`, `.complexipy.toml`, then `[tool.complexipy]`; exclude globs are root-relative and gitignore rules apply. Module-level script scoring is opt-in with `--check-script`. | CLI help confirmed the paths, threshold, `--failed`, `--top`, JSON/CSV/GitLab/SARIF, `--exclude`, diff/staged, script, and refactor options. No `[tool.complexipy]` section exists in this repository's `pyproject.toml`; the probe used CLI settings only. |
| Results | The API documents function line ranges; the guide describes JSON output. | Observed JSON records contain path, function, complexity, and refactor-plan fields, but no line positions. The API returned `line_start` and `line_end`. |
| Ruff PLR0916 | Ruff documents a preview rule for Boolean expressions in `if` statements, default limit five. Complexipy's comparison page instead discusses PLR0912. | Locked Ruff 0.16.8 is not configured to select PLR0916. An explicit scan found no repository hits. A six-expression `if` and `elif` each triggered; matching conditions in `while`, `assert`, ternary, comprehension, and match guard did not. This Boolean-expression rule measures a different property from function cognitive complexity. |
| Compatibility | PyPI metadata says Python `>=3.8` and lists CPython 3.14 wheels for macOS, Windows, and Linux variants. | On macOS 26.6.2 x86-64 (Darwin 25.6.0), CPython 3.14.8 at `.venv/bin/python`, the 8.0.1 CLI wheel and Python API ran. The CLI parsed `src`, `script`, `test`, and `example` without errors. Linux and Windows were not run. The source pins Ruff parser/AST crates to 0.12.9. |

The source boundary is the
[8.0.1 release](https://github.com/rohaquinlop/complexipy/releases/tag/8.0.1),
commit `030e207`. The score details above come from its
[`cognitive_complexity.rs`](https://github.com/rohaquinlop/complexipy/blob/030e207/src/crates/complexipy-core/src/cognitive_complexity.rs)
and
[`utils.rs`](https://github.com/rohaquinlop/complexipy/blob/030e207/src/crates/complexipy-core/src/utils.rs).
The 8.0.1 notes describe documentation-domain and sdist-license changes, not
scoring changes. Current docs may include post-release edits; where their score
claims differed, the tag source and observations are recorded separately.

Other official references: [PyPI](https://pypi.org/project/complexipy/),
[changelog](https://complexipy.com/changelog/),
[usage guide](https://complexipy.com/usage-guide/),
[score guide](https://complexipy.com/understanding-scores/),
[Ruff comparison](https://complexipy.com/comparison-with-ruff/),
[refactoring rules](https://complexipy.com/refactoring-rules/), and
[Ruff PLR0916](https://docs.astral.sh/ruff/rules/too-many-boolean-expressions/).
The usage guide documents file/directory paths, output formats, exclusions,
configuration priority, diff modes, and suggestions to flatten guards, extract
helpers, or replace eligible equality chains with `match`; source and observed
scores show why those suggestions still need human review.

## Execution record

Commands ran from the worktree root unless stated in the temporary Make target.
`uv run --no-sync python --version`
reported CPython 3.14.8 at `.venv/bin/python`; host details came from
`uname -srm` and Python's `platform.platform()`. A temporary Make extension
outside the repository wrapped these expanded commands:

```text
uv tool run --from 'complexipy>=8.0.1' complexipy --help
uv tool run --from 'complexipy>=8.0.1' complexipy --version
uv tool run --python 3.14 --from 'complexipy==8.0.1' complexipy --version
uv tool run --python 3.14 --from 'complexipy==8.0.1' complexipy $(PATHS) $(OPTIONS)
uv run --no-sync --with 'complexipy==8.0.1' python /private/tmp/complexipy-api-probe.py
uv run ruff --version
uv run ruff check --select PLR0916 $(PATHS) $(OPTIONS)
uv run --no-sync python -c 'import platform, sys; print(platform.python_implementation(), sys.version.split()[0], sys.executable, platform.platform())'
```

The lines using `$(PATHS)` and `$(OPTIONS)` are temporary Make command
templates; their values are given below. The API probe evaluated
`file_complexity("/private/tmp/complexipy-fixtures.py")`, then printed the file
score and each function's name, score, and line range. Its input and Ruff's
input are retained as text in
[probe-cases.md](probe-cases.md); these records preserve the exact snippets
without adding an executable test harness.

The representative complexipy run wrote to
`/private/tmp/complexipy-fixture-314-results.json`, then copied that file
without editing into the co-located artifact. It used
`PATHS=/private/tmp/complexipy-fixtures.py` and
`OPTIONS='--max-complexity-allowed 15 --output-format json --output /private/tmp/complexipy-fixture-314-results.json --cache-dir /private/tmp/complexipy-fixture-314-cache'`.
It returned status 0. The API probe returned status 0. The repository syntax
probe used `PATHS='src script test example'` and
`OPTIONS='--ignore-complexity --output-format json --output /private/tmp/complexipy-repo-314-results.json --cache-dir /private/tmp/complexipy-repo-314-cache --top 10'`;
it returned status 0. The console was limited to ten rows, while JSON retained
all 516 function records for later reuse; the initial scan applied no threshold.
The output was copied unchanged to the co-located repository results artifact.

The repository Ruff scan used
`PATHS='src script test example' OPTIONS='--output-format concise'` and returned
status 0 with no PLR0916 findings. The synthetic Ruff probe used
`PATHS=/private/tmp/complexipy-ruff-forms.py OPTIONS='--output-format concise'`;
Ruff reported two errors (`6 > 5`), so the Make wrapper returned status 2.
Ruff reported version 0.16.8. No project dependency or lockfile changed.

Raw machine output is retained in
[fixture results](complexipy-fixture-results.json) and
[repository results](complexipy-repository-results.json). The assessed scope is
latest-release capability, scoring behavior, syntax/platform support, and
PLR0916 overlap.

## AC-2 baseline and recommendation

The retained JSON was generated by complexipy 8.0.1 at the AC-1 assessed
revision, `ef1f6eea938b60b9a98e3c544ae1a9582ba22276`, with explicit paths
`src script test example` and `--ignore-complexity`. It contains 516 functions:
65 in `src`, 50 in `script`, 392 in `test`, and 9 in `example`. The largest
grouped scores are 360 at 0, 128 at 1–4, 21 at 5–9, one at 10, two at 13, and
one each at 15, 17, 19, and 20. The full per-score counts and names are
inspectable in [repository results](complexipy-repository-results.json).

Complexipy's maximum is inclusive: scores equal to the configured value pass;
larger scores fail. The one-time fixture used the same 8.0.1 CLI, Python 3.14,
and `--max-complexity-allowed 15`:

```text
uv tool run --python 3.14 --from 'complexipy==8.0.1' complexipy /private/tmp/complexipy-threshold-cases.py --max-complexity-allowed 15 --output-format json --output /private/tmp/complexipy-threshold-results.json --cache-dir /private/tmp/complexipy-threshold-cache --color no
```

Scores 14 and 15 passed, 16 failed, and the command exited 1. Inputs are
summarized in [probe cases](probe-cases.md); the CLI's raw JSON is in
[threshold results](complexipy-threshold-results.json).

| Maximum | Exact-score functions | Functions above maximum |
| ---: | --- | ---: |
| 10 | `prepare_project` (10) | 6 |
| 15 | `_criterion_findings` (15) | 3 |
| 17 | `check_root_owner` (17) | 2 |
| 19 | `check_work` (19) | 1 |
| 20 | `read_calls` (20) | 0 |

The highest scores represent genuine control-flow complexity, but their
responsibilities have natural boundaries. The readable-condition policy calls
for explicit boundary validation and collected diagnostics; the proposed
refactors preserve those checks while separating different jobs. A candidate
copy of each function and its cohesive helpers was parsed by complexipy 8.0.1
with a maximum of 15. The temporary copies are retained as text in
[repair candidates](complexipy-repair-candidates.txt), and the unchanged raw
scores are in
[candidate results](complexipy-repair-candidate-results.json). These are
syntax-scoring observations, not production edits or behavioral tests.
The proposed helper moves preserve the
[parent's supported-contract boundary](../README.md#shared-preservation-boundary):
accepted and rejected inputs, diagnostics and causes, safety decisions, and
effect order remain unchanged.

| Current score and function | Responsibility split | Candidate scores | Readability and preservation assessment |
| --- | --- | --- | --- |
| 20 `read_calls` | Keep log traversal in `read_calls`; move one parsed JSON record's existing validation and `UvCall` conversion to `_uv_call_from_record`. | `read_calls` 2; adapter 12. | Separates file iteration from adapting one external record. Keeps type checks, error messages, argument-before-environment validation order, and the returned tuple. |
| 19 `check_work` | Move missing, duplicate, and nonempty required-section findings to `_required_section_findings`; leave title, section indexing, criterion checks, and final sort in `check_work`. | `check_work` 9; helper 10. | Gives required-section validation a single owner and leaves the caller as orchestration. Preserves complete findings and sort order. Existing rule tests cover this output. |
| 17 `check_root_owner` | Resolve each directory entry to an optional metadata path in `_metadata_for_entry`; verify metadata symlink, file, and owner in `_verify_metadata_owner`. | `check_root_owner` 3; helpers 5 and 4. | Separates path selection from record validation. Preserves iteration order, symlink refusals, file-read order, ownership decision, and exceptions. No direct `check_root_owner` tests were found; safety cases would need focused coverage if adopted repairs proceed. |

The candidate-score command was
`uv tool run --python 3.14 --from 'complexipy==8.0.1' complexipy /private/tmp/complexipy-ac2-candidates.py --max-complexity-allowed 15 --output-format json --output /private/tmp/complexipy-ac2-candidates.json --cache-dir /private/tmp/complexipy-ac2-candidate-cache --color no --top 10`;
it returned status 0. A 15-point maximum therefore has a concrete three-function
repair inventory whose proposed responsibilities are clearer independently of
their scores. It is not chosen just because 15 is the release default.

The nearby high scores support that boundary. `Position::on_bar` in
[`broker.py`](../../../../src/ataraxia/broker.py) scores 13; its ordered
stop-loss/take-profit decisions preserve which event wins when both orders are
hit, and existing tests exercise that precedence. The test helper
[`normalize_sample_paths_and_order`](../../../../test/ataraxia/cli_sample_expected.py)
also scores 13; it validates and normalizes one output record collection while
preserving unexpected fields. Both have cohesive jobs and no evidence-backed
reason for forced extraction. In the example,
[`CrossoverRunner.__call__`](../../../../example/crossover.py) scores 8; its
short history/`None` guards precede the two mutually exclusive crossover
decisions. These are clear functions below 15. At 12, the cutoff would also
flag the two 13-point functions without a similar readability improvement.
At 17, `check_root_owner` would sit exactly at the inclusive limit despite its
clean split; 19 would leave both it and `check_work` unflagged. A limit of 20
would pass the entire baseline. The inclusive limit of 15 is a supported
boundary: it flags the three functions with justified responsibility splits,
while retaining cohesive `_criterion_findings` at 15. Limits of 13 or 14 would
also flag that cohesive stateful function.

Ruff 0.16.8's preview `PLR0916` uses a default maximum of five Boolean
expressions and targets `if`/`elif` conditions. The project has preview enabled,
but does not select this rule or override its limit. The explicit repository
scan over the same four roots returned status 0 with no findings. The AC-1
one-time forms showed six Boolean expressions in `if` and `elif` are reported,
while equivalent expressions in `while`, `assert`, a conditional expression,
a comprehension, and a `match` guard are not. This narrow rule is a possible
complement for dense `if` conditions, not a substitute for the policy's manual
review of other guards or function structure.

The baseline had no blanket test or script exclusion. A bounded root-scope probe
put a six-expression `if` function in each of `src/ataraxia`, `.cache`, and
`build`. Complexipy 8.0.1 ran on `.` with `--exclude 'build/**'` and returned
status 0; its 517 JSON records included the source probe, excluded the
Git-ignored cache probe, and excluded the build probe. Ruff 0.16.8 scanned `.`
with `PLR0916` and reported the source and build probes (status 1), but not the
cache probe. `ruff check --show-settings` confirmed the current default excludes
`.venv` and `dist`, not `build`; its resolver respects `.gitignore`. Thus the
current lint route includes Python files under `build`, while complexipy can
exclude them explicitly. A future route that excludes generated `build` and
`dist` output must apply those globs to both tools; `.venv`, `.cache`, and
Python caches already follow the repository `.gitignore`. Keep the full `src`,
`script`, `test`, and `example` scope without blanket test/script exemptions.
The complexipy path behavior comes from the tagged
[`exclude.rs`](https://github.com/rohaquinlop/complexipy/blob/030e207/src/crates/complexipy-core/src/helpers/exclude.rs)
and this temporary probe. It ran at repository `HEAD` `878e006` after the AC-1
commit; the repository Python sources were unchanged and only investigation
artifacts had been modified. Its exact commands were:

```text
uv tool run --python 3.14 --from 'complexipy==8.0.1' complexipy . --exclude 'build/**' --ignore-complexity --output-format json --output /private/tmp/complexipy-scope-results.json --cache-dir /private/tmp/complexipy-scope-cache --color no --top 3
.venv/bin/ruff check --select PLR0916 --output-format concise .
```

Complexipy returned status 0 with 517 JSON records; Ruff returned status 1 with
two findings, in `src/ataraxia/_complexipy_scope_probe.py` and
`build/complexipy-scope-probe-20261017-ac2/build_case.py`. The `build` and
`dist` directories were absent before the probe. The baseline did not enable
`--check-script`, so it scored functions rather than module-level script bodies.

**Recommendation:** use complexipy's inclusive maximum of 15 over Python
functions in all four existing roots (`src`, `script`, `test`, and `example`),
with the three focused responsibility splits above before blocking enforcement.
Pair it with Ruff `PLR0916` at its observed default maximum of five for dense
`if`/`elif` Boolean expressions. This combination addresses function control
flow and a narrower Boolean-count signal; neither is a general readability
proof. The observed match-guard Boolean gap is separate: complexipy does not
count Boolean operations inside `case` guards, and PLR0916 does not report
`match`, `while`, `assert`, conditional-expression, or comprehension guards.
Keep those forms under manual review rather than treating this coverage limit
as evidence that the function threshold is infeasible. The root-scope probe
also found that current Ruff discovery includes `build`; AC-3 must align
generated-output exclusions before adoption. No production code, dependency,
policy, or CI setting changed.
