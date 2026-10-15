# Conditional session report integration

## Purpose

Provide trustworthy private session reports only where reviewed statistics
findings establish a fitting existing method.

## Goals

- Report exact declared session scope without duplicate accounting.
- Keep unsupported measurements and pricing unknown.
- Return a no-fit result for reviewed disposition rather than build an unplanned
  collector.

## Non-Goals

- Preselect tokenuse or construct a speculative custom collector or pricebook.
- Add a telemetry framework or global usage scan.
- Run models or ingest unrelated host usage to fill measurement gaps.

## Mechanisms

- The existing method selected by reviewed statistics findings supplies
  supported measurements at the sandbox report boundary.
- Retained private execution data supplies the declared session inputs and raw
  provenance for the report.

## Acceptance criteria

### **AC-1 TODO** Report supported session and tool measurements

The refined Make/report interface delivers private reports using only a
recommended fitting existing method.

- Reports identify exact session scope, created/resumed invocations, distinct
  sessions, elapsed time, status and artifact paths.
- Supported measurements include input, cached input, output and reasoning
  tokens plus successful/failed tool counts in the Investigation's established
  units/coverage.
- Missing/unsupported values stay unknown rather than zero across
  initial/resumed, duplicate and failed records, with no repeated/resumed
  double-counting.
- Tool failure, command exit, expected nonzero denial and agent mistakes remain
  distinct, as do model calls, tool calls and tool process sessions.
- Privacy-safe raw inputs and failures stay retained, while no-fit findings
  return for reviewed disposition without an invented collector or claimed
  implementation.

### **AC-2 TODO** Label supported API-equivalent cost estimates

Any reported cost is a supported API-equivalent estimate, never inferred
subscription billing.

- Estimates identify model, pricing tier/version, date/source provenance and
  supported token categories.
- Requested and observed model/tier stay distinct, and fallback pricing
  follows verified observed identity or remains unknown.
- Arithmetic follows the declared primary source/category semantics without
  cache/reasoning double-counting, leaving missing prices or semantics unknown.

## Dependencies

- **TODO** [Session statistics Investigation](../statistics/README.md): supplies
  reviewed recommendation/coverage limits before exact interface refinement and
  review-size reassessment, then integration or no-fit disposition.
- **TODO** [Native execution and retained artifacts](../execution/README.md):
  supplies retained private execution data for declared sessions.
