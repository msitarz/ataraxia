# Parser selection investigation findings

**Recommendation:** use `markdown-it-py==4.2.0` for the work-check parser. Its
documented token stream and optional syntax tree expose block type, heading
level, nesting and line maps directly. The repository adapter still needs to
validate upstream tokens and translate them into immutable local values, but it
does not need to reconstruct Markdown structure from rendered output or infer
line numbers from character offsets.

This is a recommendation for maintainer review, not production adoption. The
parent Work owns that decision and any dependency or lockfile changes.

## Compared candidates

| Candidate and tested version | Evidence and fit | Tradeoffs |
| --- | --- | --- |
| `markdown-it-py==4.2.0` | **Best fit.** `MarkdownIt("commonmark").parse()` returned block tokens with documented `type`, `tag`, `nesting`, `level`, and source `map`; inline tokens expose the AC header's `strong_open` and text children. The public `SyntaxTreeNode` can represent nesting directly. On the adversarial fixture, quote/list headings had nonzero nesting, and comment/fence content was in `html_block`/`fence` tokens. | Tokens share one runtime class, and several fields such as `type` are plain strings, so the adapter must validate token kinds, source maps and child structure before exposing local types. It is pure Python; the tested install used a universal wheel and installed only `mdurl==0.1.2` alongside the parser. |
| `pyromark==0.9.13` | **Capable, with a source-location documentation gap.** `events()` emitted heading levels, inline emphasis/text, and explicit start/end events for block quotes, lists, items, HTML and code blocks. `events_with_range()` added integer start/end offsets. The fixtures showed all required exclusions and positive headings/declarations. Upstream publishes a typed event union and CPython 3.14 wheels. | The event stream requires a local stack to recover block nesting. Probes established that returned offsets count UTF-8 bytes: offset 54 identifies line 19 in the Unicode fixture, while treating it as a Python string index reports line 21. The installed type stub defines `Range` as two integers, but neither its units nor semantics are documented. UTF-8 newline counting matched every observed source heading. The base install added `typing_extensions==4.16.0`. |
| `cmarkgfm==2025.10.22` | **Structurally usable through rendered HTML.** `CMARK_OPT_SOURCEPOS` caused rendered block tags to carry line/column ranges. HTML nesting distinguishes quote/list descendants, `<pre><code>` retains fenced content, and inline AC text renders under `<strong>`. The adversarial fixture showed comment contents omitted as raw HTML and fake headings retained only inside their containers. | `parse_document()` returns an opaque CFFI reference annotated `Any`; the Python package does not expose typed node traversal. A supported adapter must render HTML and then build local structure with an HTML parser, adding a second parse and validation layer. The tested base environment installed `cffi==2.1.1` and `pycparser==3.11`; cmarkgfm built from source on this Intel Mac/Python 3.14.8 because PyPI's 3.14 macOS wheel listing was ARM64. |

The table separates observed probe behavior from public API documentation. In
particular, pyromark's observed UTF-8 byte offsets do not establish an upstream
guarantee for their units.

## Method and retained observations

The probes ran on CPython 3.14.8 (Darwin x86_64), satisfying the repository's
`requires-python = ">=3.14"`. Each package was installed at the pinned version
in its own temporary environment under `/private/tmp`; the repository's
dependencies and lockfile were not changed. The archived probe Makefile
contains the exact `uv venv` and `uv pip install` commands in `setup`, and
`probe-all` executes each isolated interpreter. The initial cmarkgfm install
built the sdist on this Intel Mac. The JSON records interpreter, platform,
distribution version, declared requirements and installed distribution versions.
Base requirements are `typing-extensions>=3.7.4` for pyromark, `mdurl~=0.1` for
markdown-it-py, and `cffi>=2.0.0` for cmarkgfm (with `pycparser` installed
transitively). The Makefile's setup target was rerun successfully against the
prepared environments. An initial version query found no `cmarkgfm.__version__`
attribute; the probe records the installed version through
`importlib.metadata.distribution()` instead.

The same four Markdown inputs (two real contracts plus adversarial and Unicode
fixtures) were parsed by each public API. The one-time probe source, fixtures,
and Make recipes are archived in
[commit a61f2f1](https://github.com/msitarz/ataraxia/tree/a61f2f1b662ba8a9021e77abca8adac366c46d90/doc/feat/work-contract-migration/work-check/parser-selection/probes).
These were upstream-only probes, not ongoing regression tests. To reproduce
them, create a disposable checkout of that commit with
`git worktree add --detach /private/tmp/parser-selection-replay a61f2f1b662ba8a9021e77abca8adac366c46d90`,
then run these archived Make targets from that checkout's repository root:

```sh
make -C doc/feat/work-contract-migration/work-check/parser-selection/probes setup
make -C doc/feat/work-contract-migration/work-check/parser-selection/probes probe-all
```

| Input | Provenance / coverage |
| --- | --- |
| [real-work-check.fixture](https://github.com/msitarz/ataraxia/blob/a61f2f1b662ba8a9021e77abca8adac366c46d90/doc/feat/work-contract-migration/work-check/parser-selection/probes/fixtures/real-work-check.fixture) | Exact copy of `doc/feat/work-contract-migration/work-check/README.md` at base `99df4b0e3b9632e952b0246e17e95df135204fab`; SHA-256 `7c4fd6a2a545548708390d947e0f879acd875e3cf198c433cffa2d730cf170f8`. |
| [real-evaluation.fixture](https://github.com/msitarz/ataraxia/blob/a61f2f1b662ba8a9021e77abca8adac366c46d90/doc/feat/work-contract-migration/work-check/parser-selection/probes/fixtures/real-evaluation.fixture) | Exact copy of `doc/feat/evaluation-sandboxes/lifecycle/active-state-exclusion/README.md` at the same base; SHA-256 `2d2115aca57acdf8c2a4b7e9843b96949421cfc2ef94ad98ce79e4b3640a2f06`. |
| [adversarial.fixture](https://github.com/msitarz/ataraxia/blob/a61f2f1b662ba8a9021e77abca8adac366c46d90/doc/feat/work-contract-migration/work-check/parser-selection/probes/fixtures/adversarial.fixture) | Positive top-level H1/H2/H3 and bold AC declaration; fake required section and AC headings inside a block quote and nested list; fake headings inside an HTML comment and fenced Markdown; Unicode before later content. |
| [unicode-offset.fixture](https://github.com/msitarz/ataraxia/blob/a61f2f1b662ba8a9021e77abca8adac366c46d90/doc/feat/work-contract-migration/work-check/parser-selection/probes/fixtures/unicode-offset.fixture) | Eighteen lines of `é` before a located H2, followed by enough lines that interpreting a byte offset as a character offset reports a different line. |

The archived
[probe source](https://github.com/msitarz/ataraxia/blob/a61f2f1b662ba8a9021e77abca8adac366c46d90/doc/feat/work-contract-migration/work-check/parser-selection/probes/probe.py)
records decision-relevant heading levels, source locations, container context,
AC inline structure and fence/comment evidence in `pyromark.json`,
`markdown-it-py.json`, and `cmarkgfm.json`. It omits ordinary prose tokens and
the full rendered HTML.

For markdown-it-py, source maps are zero-based half-open line intervals, so the
adapter can report `map[0] + 1`. The retained JSON records the corresponding
one-based line observed from each heading's opening token. For pyromark, the
probe converts observed UTF-8 byte offsets to lines by counting newline bytes
before each event start. In the adversarial fixture, offset 186 identifies
`## Quoted example`; slicing the Python string at 186 starts at `d example`. In
the Unicode boundary fixture, offset 54 maps to source line 19 by UTF-8 byte
counting but to line 21 if incorrectly treated as a character index. The public
docs and stubs still do not define the offset units. For cmarkgfm, the output's
`data-sourcepos` values give one-based line/column endpoints on rendered HTML
block tags. These are observations at the tested versions, not claims about
future releases.

No timing comparison was run. The small fixture probes completed without a
noticeable delay; this is not evidence about a full repository scan, and no
performance concern currently changes the recommendation.

## Public references

- [markdown-it-py 4.2.0 on PyPI](https://pypi.org/project/markdown-it-py/4.2.0/),
  [token stream and syntax tree documentation](https://markdown-it-py.readthedocs.io/en/v4.2.0/using.html#the-token-stream),
  and
  [Token API](https://markdown-it-py.readthedocs.io/en/v4.2.0/api/markdown_it.token.html).
- [pyromark 0.9.13 on PyPI](https://pypi.org/project/pyromark/0.9.13/) and
  [upstream event API example](https://github.com/monosans/pyromark#iterating-over-markdown-elements).
  The package's installed `py.typed` stubs expose the event and range types;
  range units are not documented there.
- [cmarkgfm 2025.10.22 on PyPI](https://pypi.org/project/cmarkgfm/2025.10.22/)
  documents `CMARK_OPT_SOURCEPOS` for rendered HTML; the
  [Python wrapper](https://github.com/theacodes/cmarkgfm/blob/master/src/cmarkgfm/cmark.py)
  documents `parse_document()` as returning an opaque syntax-tree reference.

## Remaining limits

This was a bounded structural comparison of two real contracts, one adversarial
fixture and one Unicode-offset fixture, not a Markdown conformance suite. It did
not test malformed UTF-8, custom parser extensions, every possible nesting
pattern, or future release compatibility. No upstream-only probe is retained as
a production regression test. The parent Work must still review this
recommendation before adoption.
