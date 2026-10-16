# Investigate Markdown parser selection

## Purpose

Determine which of pyromark, markdown-it-py, and cmarkgfm can support structural
Work checking with the least repository-owned parsing.

## Goals

- Establish each candidate's fit for the parent's required Markdown boundary.
- Recommend a parser and version with explicit tradeoffs, or report no fit.

## Non-Goals

- Implement work-check or its production parser boundary.
- Adopt a production dependency or change the dependency declarations or
  lockfile.
- Run a benchmark programme or broaden this into a general Markdown comparison.

## Mechanisms

- Focused exploratory probes compare the three candidates on shared inputs.
- Concise retained findings and probe artifacts support maintainer review.

## Acceptance criteria

### **AC-1 DONE** Candidate fit is established from comparable evidence

The comparison answers whether each candidate can supply the structure needed by
the
[parent's Markdown boundary and Work rules](../README.md#acceptance-criteria)
through documented public APIs and a simple adapter. Each candidate is checked
at a recorded version on the same representative active Work contracts and small
tricky snippets, with the inputs, method, environment, and observed execution
results retained as inspectable supporting artifacts.

- Repository Python support is checked against `requires-python`, including
  installation and probe execution on the repository's current interpreter.
- Parsed structure exposes heading levels and nesting, source locations
  sufficient for repository-relative `path:line` diagnostics, and inline
  structure sufficient to interpret AC declarations.
- Fenced code, HTML comments, block quotes, and list content cannot yield false
  top-level sections or AC declarations, with positive heading and declaration
  cases checked alongside these exclusions.
- Findings distinguish observed behavior from assumptions, unsupported
  capabilities, and remaining uncertainty, and describe required adaptations
  and their limitations without relying on undocumented internals.

Temporary probes stay outside production integration, and upstream-only probes
follow [test ownership](../../../../test-ownership.md) while retaining their
method and results, including unsuccessful results.

### **AC-2 DONE** A bounded recommendation is ready for maintainer review

Concise findings record each candidate's fit, pros, and cons and recommend a
specific parser version with its required adaptation and tradeoffs, or
explicitly conclude that none meets the mandatory capabilities. The
recommendation prefers the simplest adapter and least custom parsing, precise
public APIs and typing, clear documentation and maintenance, and low dependency
and installation overhead. Performance needs further investigation only if a
normal repository scan is noticeably slow; any such observation states its
conditions and effect on the recommendation without introducing a benchmark
programme.

The maintainer reviews the findings and recommendation before production
adoption; the
[parent Work](../README.md#ac-1-todo-adopt-the-reviewed-parser-choice) owns
dependency and lockfile adoption and the production boundary, so completing this
Investigation does not establish production readiness.
