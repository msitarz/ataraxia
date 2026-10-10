# Mermaid validation investigation

mermaidx is feasible for the exercised embedded SVG cases after building
QuickJS from its complete source checkout, but **defer checker adoption** until
setup/platform support and diagnostic requirements are resolved. The original
sdist fails setup; the original semicolon sequence fails with an opaque wrapper
exception. This is not a browser parity, visual-quality or performance result.

## Execution and reproducibility

Initial investigation used Ataraxia `c22f8c802dc4002bd630e569c60f7b40342f63f3`;
the maintainer then authorized a disposable complete-source experiment, with no
project dependency, Makefile or CI changes. CPython 3.14.6 on macOS 26.6.2
x86_64, uv 0.12.19, setuptools 84.0.0 were used. Versions, source SHAs,
release-workflow provenance and wheel hash are in
[versions.json](versions.json).

Initial setup created the disposable environment. The actual install invocation
resolving the sdist build was:

```sh
uv pip install --python /private/tmp/ataraxia-mermaid-probe-env/bin/python --cache-dir /private/tmp/ataraxia-mermaid-probe-cache mermaidx==0.9.5
```

It resolved mermaidx 0.9.5, quickjs-ng 0.17.0.1, resvg-py 0.5.0 and termaid
0.9.0. QuickJS sdist compilation failed at `upstream-quickjs/quickjs.c:76:10`
with `fatal error: 'quickjs-c-atomics.h' file not found`; Make exited 2. A
subsequent `make -f /private/tmp/ataraxia-mermaid-probe.Makefile install`
executed:

```sh
uv pip install --python /private/tmp/ataraxia-mermaid-probe-env/bin/python --cache-dir /private/tmp/ataraxia-mermaid-probe-cache --only-binary :all: mermaidx==0.9.5 quickjs-ng==0.15.1
```

Resolution reported no exact 0.15.1 version; Make exited 2.
[PyPI metadata](https://pypi.org/pypi/quickjs-ng/json) lists macOS wheels for
0.15.1.1 through 0.17.0.1 only for arm64, not x86_64; see
[release files](https://pypi.org/project/quickjs-ng/0.17.0.1/#files).
Earlier default-cache sandbox access, cached Python 3.14.7 initialization and
urllib certificate failures were preparation failures, not diagram failures.

Complete-checkout commands cloned wrapper v0.17.0.1 at `f2ac026f...`,
initialized its upstream submodule, checked upstream v0.17.0 at `6d46d07d...`,
and changed only pyproject version 0.12.1.1 to 0.17.0.1. This follows its
[pinned release workflow](https://github.com/genotrance/quickjs-ng/blob/f2ac026f5105b492b15b331bf1b71bd7a4e9cfb2/.github/workflows/build.yml)
and was explicitly authorized; C/Python implementation was unchanged. Actual
temporary `probe.mk` targets `setup build`, `install info`, and `run` under
`/private/tmp/ataraxia-mermaid-complete-experiment` exited 0. Build/install
recipes are retained in [probe.mk](probe.mk). On fresh disposable paths:

```sh
make -f doc/feat/mermaid-validation/investigation/probe.mk source setup build
make -f doc/feat/mermaid-validation/investigation/probe.mk install info run
```

The retained recipe adds an explicit constraint for the observed build backend;
that constrained recipe itself has not been rerun. Actual `mermaidx --info`
returned **Mermaid 11.16.0**, with backend explicitly `quickjs`. Each diagram
was forced through `.svg()` in a fresh child with 30-second timeout; all
completed before timeout. SVG hashes, exits and diagnostics are in
[results.json](results.json). Root independently reran `info/run` and verified
the wheel hash with the same outcome matrix. Retained results are that reviewer
rerun: class SVG was 16700 bytes, versus 16691 initially. Sizes and output
hashes are observations, not deterministic expectations; the success/error
matrix was reproduced. No official CLI/browser or GitHub live-version probe was
run.

## Observed matrix

| Input | Embedded SVG observation |
| --- | --- |
| [Original full sequence](sequence-original.mmd), historical fence at 61f1b2ae... | Exit 1, TypeError `Unknown quickjs tag: -6`, no useful source location. |
| [Corrected full sequence](sequence-corrected.mmd), fence at 03d32142... | Exit 0, SVG 42665 bytes. |
| Valid sequence / class / state / flowchart in [inputs.json](inputs.json) | Exit 0, SVG 22230 / 16700 / 7479 / 10695 bytes. |
| Malformed sequence | Exit 1, Mermaid parse error on diagram line 2, expected actor token, got NEWLINE. |
| Multiple-fence Markdown | Harness extracts content starting at Markdown 4 and 9; first SVG succeeds, second fails at diagram 2 (Markdown 10). |
| No-diagram Markdown | Harness finds zero fences and succeeds; candidate is not called. |

[probe.py](probe.py) provides fixture-only extraction, not mermaidx native
Markdown support or production extraction validation. Its runner exits 0 after
recording individual failures. `render()` is lazy: construction alone is not
parsing evidence. Successful `.svg()` proves embedded rendering; malformed input
exposes parse diagnostics inside rendering. No standalone parse-only API,
visual inspection, PNG quality or browser renderer equivalence was established.

## Candidate and compatibility assessment

| Candidate | Fit, dependencies and uncertainty |
| --- | --- |
| [mermaidx 0.9.5](https://pypi.org/project/mermaidx/0.9.5/) | Bundled Mermaid JS/QuickJS and DOM shim; actual matrix above. ASCII has a separate parser. Python 3.9+/OS-independent metadata does not establish native dependency availability. Complete-source bootstrap is additional maintenance. |
| [Official CLI](https://github.com/mermaid-js/mermaid-cli) | Browser rendering via Puppeteer; Node/browser requirements. Source read 2026-10-10 declared CLI 12.0.0, Mermaid `^12.0.0`, Node `>=22.13.0`, Puppeteer `^25.0.0`; not installed/resolved versions. mmdc/browser unavailable, all cases unexercised. |
| [pymermaider](https://github.com/diceroll123/pymermaider) | Rust generator of class diagrams from Python code, not an existing-fence validator; exclude. Documentation only, no execution/version claim. |

Projects declare MIT; adoption must inspect transitive licenses. Release/source
activity exists, but this inspection does not establish maintenance longevity.
Only x86_64 execution was verified. Local wheel is tagged universal2 and file
inspection shows two Mach-O slices, but linker warned x86_64 objects were
ignored for arm64; usable arm64 output is unverified. Linux CI, Windows, clean
offline setup and diagnostic stability remain unverified. No browser/Node/system
install or upstream implementation repair occurred. Logs remain in the
disposable experiment directory; pertinent failures and warnings are retained
here.

[GitHub guidance](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
recommends a fenced `info` diagram for its live Mermaid version, unavailable
here. Engine11.16.0 does not establish GitHub parity; DOM/config/fonts and
supported diagram types may differ even at matching versions.

## Proposed bounded adoption contract

Before adoption, authorize a bounded compatibility/setup Work proving pinned
Python 3.14 installation on supported platforms and offline execution after
setup; resolve source-wheel maintenance and opaque-error diagnostic fallback.
Preserve unknown browser/GitHub parity unless separately exercised.

Then integrate one fenced-Markdown boundary into existing `make doc-check`. Make
currently runs rumdl checking of selected paths plus `.` for link-graph checks
and formatting checks of selected `ARGS` paths. `verify-check` calls
`doc-check ARGS=`; `ci-check` reaches it through Check CI. Preserve those
defaults, add Mermaid inspection once at that owner, and emit no checkout
artifacts.

Proposed validation: extraction tests cover multiple fences/no-diagram success;
actual backend integration rejects malformed first/later fences and the original
sequence, accepts the corrected/valid fixtures, reports file/fence and mapped
Markdown lines when engine locations exist, and gives a fence-level fallback for
opaque failures. Aggregate errors, distinguish setup/syntax/rendering or
unsupported-type failures, exit nonzero on any failed fence and zero without
diagrams. Prove `ARGS` limits Mermaid inspection, default CI checks all
Markdown, and bounded offline execution. These requirements are not adopted or
implemented.
