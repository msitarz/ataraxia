# Conditional session report integration

Depend on reviewed [statistics findings](../statistics/README.md) and
[retained execution data](../execution/README.md). Integrate only the
recommended fitting existing method at the sandbox reporting boundary; keep the
report on the private side. If none fits, record the limitation and return for a
reviewed disposition rather than build an unplanned collector. Before execution,
refine the exact Make/report interface from the recommendation and reassess
review size. No tokenuse adoption, new telemetry framework or global usage scan
is preselected. Do not construct a speculative custom collector or pricebook.

## Acceptance

- **AC-1 TODO** The report includes exact session scope, created versus resumed
  invocations and distinct sessions, elapsed time/status/artifact paths, input,
  cached input, output and reasoning tokens, plus successful/failed tool counts
  where supported. Missing/unsupported values remain unknown, not zero; resumed
  or repeated records are not double-counted. Tool failure status, command exit,
  expected nonzero denial probes and agent mistakes remain distinct, as do model
  calls, tool calls and tool process sessions.

  Validation: criterion-marked Make/report-boundary tests compare complete
  expected reports from small independently reviewed privacy-safe event inputs,
  including resumed/duplicate, failed and missing-data cases. Independent review
  verifies the selected tool's actual coverage and units against Investigation
  limits. Reuse existing helpers; do not overvalidate fixture schemas or add
  upstream-only fixtures.
- **AC-2 TODO** Any cost is labeled an API-equivalent estimate with model,
  pricing tier/version, date/source provenance and supported token categories.
  Requested and observed model/tier are distinguished; fallback-model pricing
  follows verified observed identity or remains unknown.
  Subscription billing is not inferred; absent prices/category semantics leave
  cost unknown and reasoning/cache treatment cannot silently double-count usage.

  Validation: independently verify the declared primary pricing source and
  bounded arithmetic examples; criterion-marked tests cover unavailable prices,
  category overlap and provenance. Reporting preserves raw inputs and failures,
  with no model runs or unrelated host usage ingestion to fill measurement gaps.
