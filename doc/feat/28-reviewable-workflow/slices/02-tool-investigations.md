---
id: F28-02
kind: slice
parent: F28
status: proposed
approved_revision: null
---

# Investigate tools before selecting gates

## Outcome and scope

Give the defining session explicit investigation steps. Each produces a small
evidence artifact and a reviewed adopt, adapt, reject, or defer recommendation.
Keep probes isolated from production dependencies. Agree a time or experiment
budget per question; stop with honest partial findings if it is exhausted.

Record pinned source/package versions, Python and uv versions, environment and
platform, commands, expected versus observed results, relevant output, costs,
and remaining uncertainty. Search primary documentation, code, releases, issues,
and credible alternatives. A README claim is not runtime compatibility evidence.

## Proposed iterations

| Step | Question and concrete artifact | Verification and proposed checkers |
| --- | --- | --- |
| 1 | Can pinned rumdl cover Markdown hygiene, links/anchors, required headings and frontmatter key rules without noisy rewrites? Present a capability/false-positive matrix | Probe valid/invalid links, duplicate headings, code spans/fences, tables, absent frontmatter, missing keys and bad field values; run rumdl on representative docs |
| 2 | Which parser/schema combination supports strict kind-specific YAML and accurate source locations with the smallest custom layer? Present two representative schemas and diagnostics | Probe YAML scalar ambiguity, quoted full SHAs, duplicate keys/IDs, missing fields, enums and cross-file references; compare JSON Schema and typed validation candidates |
| 3 | Which maintained ASD-STE100 candidates are suitable, and can sourdough work on the pinned toolchain? Present a short shortlist, reproducible compatibility findings and rejection reasons | STE correct/incorrect fixtures, fresh uv environments, model persistence, cold/offline runs and exit/output checks; investigate the reports below |
| 4 | Which mechanical style rules meaningfully help structural review? Present existing-code findings and narrow proposed thresholds | Trial Ruff `PLR0915` and `C901`, module/type cases and false positives; keep cohesion and semantic equivalence as human checks |

Treat these as multiple review iterations, not one tool-selection batch. Separate
STE installation, Markdown handling, and language quality when their evidence
does not fit one short artifact. Tool selection requires maintainer review before
dependency or CI changes. Relevant ADR eligibility is assessed independently.

## Initial sources and unanswered probes

[rumdl MD072](https://github.com/rvben/rumdl/blob/main/docs/md072.md) documents
key ordering and required keys for existing frontmatter. It does not require
frontmatter to exist or validate this workflow's field types and values. Verify
the selected release; schema validation still needs a separate layer.

Investigate [sourdough-bread/asd-ste100-checker](https://github.com/sourdough-bread/asd-ste100-checker)
explicitly and search alternatives. The initial source inspection used commit
`e193ecdd66b09ce81b7c611f1c841efd8ba84cc7`. Its README describes CLI, JSON/SARIF
output, procedure/description profiles, a spaCy model, and a technical glossary.
These make it a candidate, not an adopted dependency or proof of STE compliance.

Two open reports were read on 2026-09-29:

- [Issue 2](https://github.com/sourdough-bread/asd-ste100-checker/issues/2) reports
  that README package-name commands cannot find a published PyPI package.
  Check current releases/index availability separately from Git installation.
- [Issue 3](https://github.com/sourdough-bread/asd-ste100-checker/issues/3) reports
  that setup in uv tool environments delegates model installation to a bare uv
  command without targeting the interpreter. Reproduce the diagnosis before
  choosing a workaround or adaptation.

Neither report has been reproduced locally. Test a pinned Git source if necessary,
and compare `uv tool`/`uvx` isolation with a locked project environment on the
repository's pinned uv and Python. Check where the model is installed, whether
setup and execution use the same interpreter, and whether a fresh cache breaks
the result. Do not rely on undocumented global pip state or runtime downloads.

Probe Markdown frontmatter, headings, code, URLs, tables, mixed prose/procedures,
multiword technical terms, and original-file diagnostic locations. Determine
whether an adapter is needed; do not assume Markdown file support means prose
extraction. Evaluate supported rules against known valid and invalid sentences,
false positives, startup/run cost, rule configuration, model pinning, and
maintainability. Resolve dictionary/data provenance and redistribution suitability
for the project's intended use before adoption; consult primary terms rather
than infer permission from the code license. Unslop remains excluded.

## Acceptance criteria

| ID | Preconditions and action | Observable outcome | Verified by |
| --- | --- | --- | --- |
| AC-1 | Review each tool question's evidence artifact | Commands, pinned inputs, observed results and limits support a specific recommendation | Manual evidence review and reproducible probes |
| AC-2 | Exercise rumdl and candidate schemas on fixtures | Generic rules and semantic gaps are identified without promising untested capabilities | Recorded fixture runs |
| AC-3 | Investigate sourdough and credible STE alternatives | Current package availability and uv/model behavior are established or explicitly unresolved; Python compatibility and Markdown behavior are tested | Isolated probe logs and source references |
| AC-4 | Compare STE language quality and selected Ruff rules | Coverage, false positives, configuration and costs inform a reviewed selection, adaptation, rejection or deferral | Representative corpus report and maintainer decision |

## Next review

Record findings and approved choices in the [journal](../journal.md). Revise
affected design/slice contracts before implementing changed choices. If no
suitable STE engine exists, propose a scoped deferral; do not make a missing
required checker silently pass.

## Optional future review aid

Consider [calldiff](https://github.com/tanishqkancharla/calldiff) and its
[agent skill](https://github.com/tanishqkancharla/calldiff/blob/main/skills/calldiff/SKILL.md)
after the core workflow gates. It compares syntactic call relationships across
Git revisions, supports Python, and exposes structured output. A future probe
could assess whether that output supports a compact Mermaid view of code changes.

Use a pinned version and exact reviewed commits. Test missing or incorrect edges
for Python protocols, callbacks, decorators and process boundaries, plus changes
inside functions that preserve their calls. Check entrypoint scoping, source
locations, grammar setup and cold/offline operation. Measure whether the result
helps the maintainer review one small change. This remains an optional candidate;
it has not been installed or tried here and does not add a required delivery step.
Keep outputs as revision-linked review artifacts for the maintainer's own tools,
following the existing review entry-point contract.
