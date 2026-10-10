# Mermaid validation investigation

Do not adopt a checker yet. The available Python candidate failed setup on the
actual Python 3.14/macOS x86_64 environment; no matrix parsing or rendering was
executed. A separate bounded compatibility/probe Work is needed before choosing
a backend. This is an inconclusive feasibility result, not a tool benchmark.

## Observed preparation and retained inputs

Source inspection and preparation occurred 2026-10-10, from Ataraxia
`c22f8c802dc4002bd630e569c60f7b40342f63f3`. uv was 0.12.19;
explicit interpreter `/usr/local/bin/python3.14` reported CPython 3.14.6.
The native extension build selected macOS x86_64 (universal2 Python).
No project dependency, lock, Makefile, CI, browser or Node installation changed.

Reproduce preparation with a fresh disposable environment:

```sh
make -f doc/feat/mermaid-validation/investigation/probe.mk setup
make -f doc/feat/mermaid-validation/investigation/probe.mk install
```

The actual initial disposable Makefile install pinned `mermaidx==0.9.5` and
resolved quickjs-ng 0.17.0.1, resvg-py 0.5.0 and termaid 0.9.0. The retained
recipe pins those resolved versions. mermaidx/resvg downloads succeeded; the
QuickJS source build failed in `upstream-quickjs/quickjs.c:76:10`:
`fatal error: 'quickjs-c-atomics.h' file not found`. Setup exited 2 through
Make. Thus no Mermaid engine was actually used; `--info` never ran.
[versions.json](versions.json) retains release-artifact hashes and the inspected
bundled JS hash without treating source inspection as engine execution.

A binary-only attempt using the declared minimum literal `quickjs-ng==0.15.1`
used `make -f /private/tmp/ataraxia-mermaid-probe.Makefile install`, whose
recipe executed:

```sh
uv pip install --python /private/tmp/ataraxia-mermaid-probe-env/bin/python --cache-dir /private/tmp/ataraxia-mermaid-probe-cache --only-binary :all: mermaidx==0.9.5 quickjs-ng==0.15.1
```

It failed resolution with `there is no version of quickjs-ng==0.15.1`; Make
exited 2. [PyPI release metadata](https://pypi.org/pypi/quickjs-ng/json)
contains no exact 0.15.1 release. It lists 0.15.1.1 through 0.17.0.1 macOS
wheels only for arm64, not x86_64; see also the
[0.15.1.1 release files](https://pypi.org/project/quickjs-ng/0.15.1.1/#files)
and
[0.17.0.1 release files](https://pypi.org/project/quickjs-ng/0.17.0.1/#files).
No upstream patch, architecture switch or compiler dependency repair was tried.
Earlier preparation attempts also hit sandbox cache/tool-directory access, a
broken automatically selected cached Python 3.14.7, and unavailable offline
cache. Explicit Python and isolated cache resolved those preparation choices;
Python urllib metadata lookup separately failed certificate verification, while
curl fetched PyPI metadata successfully. These are not diagram failures.

[Original sequence input](sequence-original.mmd) is the exact fence from
`61f1b2ae0c1a5a737249e2f52e747c1aef5bc4f2`; the
[corrected conjunction input](sequence-corrected.mmd) is the exact fence from
`03d321429c71428dafdbc6e3af2e1127ba2bb641`, both at
`doc/feat/work-tree-delivery/README.md` in Git. Other exact small inputs are in
[inputs.json](inputs.json): valid sequence/class/state/flowchart, malformed
sequence, a Markdown file with valid first and malformed second fence, and a
file without diagrams. **Every matrix case is unexercised for every candidate.**
There are no observed syntax diagnostics, fence line mappings, SVG artifacts,
or no-diagram success results. The historical failure/correction is seed
context, not newly reproduced evidence.

## Candidate assessment from primary sources

| Candidate | Fit and limits | Execution evidence |
| --- | --- | --- |
| [mermaidx 0.9.5](https://pypi.org/project/mermaidx/0.9.5/) | Python wrapper using bundled Mermaid JS in QuickJS with a DOM shim; SVG generation would exercise rendering, not just syntax recognition. `render()` is lazy; force `.svg()` or `.save()`. ASCII uses a different parser and cannot establish Mermaid JS acceptance. | Setup failure above. No engine version observed or rendering coverage established. |
| [Official Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) | Official browser rendering via Puppeteer; closer browser semantics but entails Node and browser setup. Package source inspected on this date declares CLI 12.0.0, Mermaid `^12.0.0`, Node `>=22.13.0` and Puppeteer `^25.0.0`; these are source declarations, not resolved installed versions. | `mmdc` absent; no available browser. Not installed or exercised. |
| [pymermaider](https://github.com/diceroll123/pymermaider) | Rust tool generating Mermaid class diagrams from Python source, rather than validating existing fenced Markdown. Reject as the checker candidate. | Documentation assessment only; no installed version or matrix results. |

All three projects declare MIT licenses. mermaidx metadata declares Python
3.9+ and OS independence, but native dependencies determine actual platform
support; observed Python 3.14 setup failure contradicts assuming universally
usable wheels. Linux CI and Windows were not exercised. Official CLI and
pymermaider Python 3.14/platform usability remain unverified. Active source and
release artifacts exist, but maintenance longevity and diagnostic stability
are not established by this small inspection. A later Work must pin actual
package/engine/source revisions, inspect transitive licenses and supported
platform setup, and prove offline execution after preparation.

[GitHub guidance](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
requires fenced `mermaid` and recommends rendering `info` to observe its live
Mermaid version. That live result was unavailable. Neither a bundled Mermaid
v11 claim nor current CLI package declarations establish GitHub parity. Even
matching versions would not establish DOM/config/font or diagram-type parity.

## Proposed bounded adoption contract

First authorize a compatibility/probe Work with no production adoption. It must
resolve a pinned Python 3.14 backend on supported platforms without accidental
browser/Node requirements, observe its Mermaid engine version, and execute the
retained matrix. Report syntax recognition separately from SVG production;
compare original and corrected sequence outcomes without assuming acceptance.
If browser comparison is authorized, freeze official CLI/browser/engine versions
and retain differences. Unknown GitHub compatibility stays explicit.

Only after that evidence supports selection, define adoption as one Markdown
validation boundary under `make doc-check`. Current Make owns rumdl checking
of selected paths plus `.` for local-link graph checks, and formatting checks
of selected `ARGS` paths. `verify-check` calls `doc-check ARGS=`; `ci-check`
reaches it through the Check job. Preserve those paths/defaults and add Mermaid
checking once at that owner, without emitting diagram files into the checkout.

Proposed acceptance/validation: extraction tests cover fenced Mermaid, multiple
fences and no-diagram success; actual selected-backend integration tests reject
malformed first/later fences and reproduce the sequence defect with stable
repository file and Markdown line diagnostics. Map engine-relative locations
through fence starts, identify the fence when no engine line exists, aggregate
multi-fence errors, and distinguish setup/unsupported-type/rendering failure
from syntax failure. Prove nonzero exit on any failed fence and zero for a file
without diagrams. Prove `ARGS` restricts Mermaid inspection while default CI
checks all Markdown, offline after setup, with bounded per-diagram execution.
Pin setup/lock requirements and document coverage and GitHub limits. These are
proposed requirements, not implemented or observed outcomes.
