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

The refined Make/report interface integrates only the recommended fitting
existing method and keeps output private. It reports exact session scope,
created versus resumed invocations and distinct sessions, elapsed time, status,
artifact paths, input, cached input, output and reasoning tokens, and
successful/failed tool counts where supported. Coverage and units agree with
reviewed Investigation limits for initial/resumed, duplicate, failed and
missing-data records. Missing/unsupported values remain unknown, not zero;
repeated/resumed records are not double-counted.

Tool failure, command exit, expected nonzero denial probes and agent mistakes
remain distinct, as do model calls, tool calls and tool process sessions. Raw
privacy-safe inputs and failures remain retained. If no existing method fits,
the limitation returns for reviewed disposition rather than inventing a
collector or claiming report implementation.

### **AC-2 TODO** Label supported API-equivalent cost estimates

Any cost is labeled an API-equivalent estimate with model, pricing tier/version,
date/source provenance and supported token categories. Requested and observed
model/tier remain distinct; fallback pricing follows verified observed identity
or remains unknown. Arithmetic agrees with the declared primary source and
category semantics without double-counting cache/reasoning usage. Missing prices
or category semantics leave cost unknown; subscription billing is never
inferred.

## Dependencies

- **TODO** [Session statistics Investigation](../statistics/README.md): supplies
  reviewed recommendation/coverage limits before exact interface refinement and
  review-size reassessment, then integration or no-fit disposition.
- **TODO** [Native execution and retained artifacts](../execution/README.md):
  supplies retained private execution data for declared sessions.
