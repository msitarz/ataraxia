# Proposed standalone quota connection scenarios

These intent-only scenarios accompany the proposed architecture. They are not
runtime behavior or acceptance evidence. AC-6 remains TODO.

## An exhausted invocation with no quota rows

- **Given** quota waiting is enabled, the first evaluation's correlated session
  has valid supported identity metadata but no quota rows, and its complete
  safely settled output matches the proposed narrow exhaustion sequence.
- **When** its scope is pinned and its attempt and association are persisted.
- **Then** dispatch pauses, active attempts drain, and the coordinator waits
  without inventing window percentages or reset hints.
- **When** a separate supervised probe reports fresh complete availability for
  the same scope and its evidence is persisted.
- **Then** the coordinator resumes eligible no-result calls with their frozen
  inputs, without repeating completed calls.

## A probe remains exhausted without numeric windows

- **Given** a durable scoped quota trigger and remaining probe budget.
- **When** a probe produces the recognized exhaustion sequence and matching
  session identity but no numeric windows.
- **Then** its evidence records exhausted state with unknown windows and hints,
  and the existing bounded polling cadence continues.

## A different or unavailable identity

- **Given** a reader has pinned the first validated evaluation scope.
- **When** another active evaluation or a probe has a different validated
  scope, including while the coordinator is draining.
- **Then** it latches stop, settles active work, and never resumes dispatch.
- **When** the trigger's or probe's identity is missing, ambiguous, or invalid.
- **Then** it cannot establish a scoped trigger or availability and recovery
  stops without guessing an account.

## Ambiguous output or unavailable positive evidence

- **Given** a safely settled nonzero evaluation whose output is truncated,
  malformed, has an item or unknown event, contains stderr, uses an unsupported
  version, or does not match the recognized error form.
- **When** the classifier assesses it.
- **Then** it does not infer quota retry eligibility or absence of a result.
- **Given** a scoped quota wait.
- **When** a probe has missing, stale, malformed, or mismatched positive window
  evidence, or its evidence cannot be recorded.
- **Then** it cannot authorize resumption; recovery stops incomplete.

## No opt-in or dry run

- **Given** quota waiting is disabled or the invocation is a dry run.
- **When** the standalone command runs.
- **Then** it reads no session files and launches no quota probes.
