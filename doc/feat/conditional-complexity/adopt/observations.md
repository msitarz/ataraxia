# Adoption route observations

These one-time observations use the locked Complexipy 8.0.1 and the real Make
lint route. Temporary threshold and scope probes were removed after the runs;
retained routing and configuration regressions live in
[`test/make/integration/test_routing.py`](../../../../test/make/integration/test_routing.py).
The product-source baseline was `87de7e355a36ab4d4a734198ebfddbe9f172876a`,
before AC-3 repairs; AC-2 Make and configuration edits were present in the
worktree, while the three scored functions remained unchanged.

Both `UV_NO_SYNC=true make lint ARGS=example/crossover.py` and
`make lint-check ARGS=example/crossover.py` completed successfully. The native
CLI's plain output gave `CrossoverRunner::__call__` a score of 8.

A temporary function with five nested `if` clauses scored exactly 15 in
`.venv/bin/complexipy /private/tmp/complexipy-exact.py --failed=false --plain`.
Running `make lint-check ARGS=/private/tmp/complexipy-exact.py` returned 0,
confirming the inclusive boundary through Make. The temporary file is no longer
present. Its scoring body was:

```py
"""One-time exact-threshold route probe."""


def exact(values: tuple[bool, ...]) -> int:
    """Exercise an exact score of fifteen.

    Returns:
        The number accumulated along the true nested path.
    """
    result = 0
    if values[0]:
        result += 1
        if values[1]:
            result += 1
            if values[2]:
                result += 1
                if values[3]:
                    result += 1
                    if values[4]:
                        result += 1
    return result
```

For the Ruff complement, `UV_NO_SYNC=true make lint-check
ARGS=/private/tmp/plr0916-probe.py` returned Make status 2 at the Ruff step. A
temporary `if` condition with six Boolean expressions produced only
`PLR0916: Too many Boolean expressions (6 > 5)`; Complexipy was not invoked.
That probe is also removed.

Full `make lint-check` passed Ruff, then returned Make status 2 when Complexipy
found the three baseline violations. Its console identified the file, function,
and score; `.cache/complexipy.sarif` contained the corresponding function line
ranges:

| File | Function | Score | SARIF lines |
| --- | --- | ---: | ---: |
| `script/sandbox.py` | `check_root_owner` | 17 | 335–357 |
| `script/work_check/rules.py` | `check_work` | 19 | 51–98 |
| `test/make/support.py` | `read_calls` | 20 | 24–48 |

For scope, identical temporary 21-point functions were placed under `script`,
`build`, `dist`, and `.cache`. A full `make lint-check` included the `script`
probe and omitted the other three, while retaining the three baseline findings.
Ruff passed that run. The temporary probes and newly created `build` and `dist`
directories were then removed. Existing script and test functions remain in
the assessed scope. Each file had a module docstring, a Google Returns
docstring, a `scope_probe` function, and the same nested body above with one
more guard (`values[5]`) and one corresponding increment; Complexipy reported
21.
