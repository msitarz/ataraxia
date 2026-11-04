# Initial static corpus

The private reference has a [reference-only freeze](reference-freeze.md).
The corpus and complete inputs have not been frozen for a trial; this record
does not authorize model trials. The three Python files are source
material stored as data, not runnable project modules. Private controls and
their rationales are held separately from model-visible inputs.

The source files are newly authored freight-dispatch examples. They are not
extracted from historical incidents and do not establish incident diversity.
The rule files copy the indicated passages from `doc/engineering.md` at base
revision `30155f93e89e47cf0ffb580677277e0ae786eabf`:

- [R1 guidance](r1/rule.txt): lines 144–180.
- [R3 guidance](r3/rule.txt): lines 264–290, with separately delimited context
  from lines 144–180 and the illustration at lines 182–235.
- [R4 guidance](r4/rule.txt): lines 102–112, 170–180, and 292–316, with
  separately delimited context from lines 19, 102–112, and 144–180.

The copies retain exceptions and operation-specific error guidance; no
objective deterministic-tool exclusions have been applied. These copies do not
replace the guidance owner. Counts use Python `splitlines()` and count lines for
which `line.strip()` is nonempty, including comments, docstrings, imports, and
code.

| Rule | Source | Nonblank lines |
| --- | --- | ---: |
| R1 | [Dispatch](r1/dispatch.py.txt) | 364 |
| R3 | [Planning](r3/planning.py.txt) | 301 |
| R4 | [Ledger](r4/ledger.py.txt) | 381 |

The reference review assessed applicability, context sufficiency, and the
separately held rationales. A complete input freeze requires further review.
[Draft packets and prompts](../inputs/preparation.md) are prepared separately.
Call lists, runtime binding, invocation protections, and model trials remain
outside this draft. These authored examples do not complete any Evaluation
acceptance criterion or support a production granularity decision.
