# Simplify acceptance tooling

## Purpose

Remove obsolete acceptance tooling and test-to-AC bookkeeping without losing
ordinary regression coverage.

## Goals

- Retire pytest covers markers and acceptance-specific test selection.
- Retire ac-check and its obsolete declaration parser completely.
- Preserve normal test discovery and behavior regression coverage.

## Non-Goals

- Infer semantic coverage, judge outcome quality, or enforce every template
  section.
- Add a replacement runner, mapping file, or permanent dual-format support.
- Remove tests merely because they once carried covers markers.

## Mechanisms

- Existing Make test commands select relevant paths and pytest cases.
- Existing acceptance scripts, fixtures, and orphan helpers are removed with
  their retired interfaces.

## Acceptance criteria

### **AC-1 DONE** Marker-based selection retired

Make no longer exposes ac-collect or ac-test, pytest no longer registers covers,
and test decorators no longer refer to Work/AC identifiers. Obsolete selector
code, fixtures, and tests are removed; imports and shared helpers are retained
only for surviving callers. Behavioral tests keep their assertions and execution
scope unless they solely exercise the retired infrastructure. Normal product,
script, Make, and example test routes continue to work.

### **AC-2 TODO** Obsolete declaration checker retired

Make no longer exposes ac-check. `script/acceptance_coverage.py`, its dedicated
tests and fixtures, and obsolete declaration/Validation parsing are removed.
The orphan `script/work_paths.py` helper and its dedicated tests leave with its
last callers. Current guidance, reminders, and callers no longer advertise or
invoke any retired acceptance command. This Work introduces no replacement
checker; the sibling [work-check Work](../work-check/README.md) owns that tool.

### **AC-3 TODO** Tests cover the surviving tooling behavior

Surviving Make guidance and test-routing behavior remains covered without
obsolete marker, selector, declaration-parser, or orphan-path-helper
expectations. Fixture and helper cleanup leaves unrelated tooling tests usable.
Ordinary test commands collect and execute the relevant surviving tests without
markers.

## Dependencies

- [Work acceptance](../../../acceptance-tracing.md) and the
  [contract template](../../../work-contract-template.md): supply the delivered
  evidence and authoring rules. Coordinate further guidance/reminder edits with
  the migration owner.

## Links

- [Initial inventory](../inventory.md): current scripts, targets, and test
  surfaces.
