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
all 516 function records for later reuse; no baseline distribution or threshold
assessment was performed. The output was copied unchanged to the co-located
repository results artifact.

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
PLR0916 overlap. Threshold/readability recommendation and integration
feasibility belong to AC-2 and AC-3, respectively.
