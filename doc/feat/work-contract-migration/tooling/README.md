# Simplify acceptance tooling

## Purpose

Remove test-to-AC bookkeeping while keeping only acceptance checks that provide
useful feedback on the new contracts.

## Goals

- Retire pytest covers markers and acceptance-specific test selection.
- Support heading-based criteria without Validation-clause parsing.
- Preserve normal test discovery and behavior regression coverage.

## Non-Goals

- Infer semantic coverage, judge outcome quality, or enforce every template
  section.
- Add a replacement runner, mapping file, or permanent dual-format support.
- Remove tests merely because they once carried covers markers.

## Mechanisms

- Existing Make test commands select relevant paths and pytest cases.
- Existing acceptance scripts and fixtures are reduced or removed according to
  the retained command surface.

## Acceptance criteria

### **AC-1 TODO** Marker-based selection retired

Make no longer exposes ac-collect or ac-test, pytest no longer registers covers,
and test decorators no longer refer to Work/AC identifiers. Obsolete selector
code, fixtures, and tests are removed; imports and shared helpers are retained
only for surviving callers. Behavioral tests keep their assertions and execution
scope unless they solely exercise the retired infrastructure. Normal product,
script, Make, and example test routes continue to work.

### **AC-2 TODO** Declaration checking matches the new contract

If retained, `make ac-check WORK=path/to/README.md` recognizes heading
declarations such as `### **AC-1 TODO** Outcome`, handles nested explanatory
headings, rejects malformed/duplicate IDs and missing names, and ignores
fenced/commented examples. It neither scans tests nor parses Validation clauses
nor claims completion from DONE labels. Work inputs identify `README.md`
contracts only; path safety remains intact. Support for separate specification
contracts is removed with its obsolete cases. A decision to remove ac-check
instead is explained in the reviewed change and reflected consistently in
guidance and callers; no replacement checker is introduced.

### **AC-3 TODO** Tests cover the surviving tooling behavior

Focused tests exercise the retained Make boundary and meaningful parser/path
failure cases, without preserving obsolete marker/selector expectations.
Fixtures and helper cleanup leaves other tooling tests usable. Ordinary test
commands collect and execute the relevant surviving tests without markers.

## Dependencies

- [Work acceptance](../../../acceptance-tracing.md) and the
  [contract template](../../../work-contract-template.md): supply the delivered
  evidence and authoring rules. Coordinate further guidance/reminder edits with
  the migration owner.

## Links

- [Initial inventory](../inventory.md): current scripts, targets, and test
  surfaces.
