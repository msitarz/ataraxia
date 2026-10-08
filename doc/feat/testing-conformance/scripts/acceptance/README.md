# Acceptance tooling testing boundaries

Clean acceptance selection and declaration tooling under the parent
[script testing contract](../README.md); preserve command behavior, static-only
reporting, historical markers and exact refusals. No production API, tool
policy or new framework changes belong here.

## Delivery map

- **DONE** Command construction: typed isolated tests preserve complete pytest
  argv for both roots and exact invalid Work/criterion refusals.
- **DONE** Command summaries: typed unit cases preserve the exact missing-WORK
  response and distinguish empty from selected pytest summaries.
- **DONE** Declaration parsing: typed tests preserve malformed declaration
  outcomes, exact syntax diagnostics, and legacy/outdented annotation behavior.
- **DONE** Declaration reports: typed cases preserve neutral status/method/
  marker reports across TODO/DONE and unchanged input files.
- **TODO** [Static marker discovery](marker-discovery/README.md): decorated
  candidate selection, literal marker validation, and exact diagnostics.

Sequence command construction before summaries, then parsing before reports and
marker discovery. Each complete diff, including types, fixtures and strict
inclusion, must fit the five-minute review target; split before expansion.

Use public script functions. Justify and scope any sibling-import or root setup;
do not patch internal call graphs. The two current test files are historical
containers, not whole-module ownership: extract only each leaf's cases into
cohesive typed modules and strictly include only owned modules/helpers. Command
construction owns the command-script import/root setup reused narrowly by
summaries; parsing owns equivalent checker setup reused by later declaration
leaves. No new framework. Units start no processes; run Make acceptance tests
after shared support or fixture changes.

Use distinct test/example roots and named, typed source fixtures copied
unchanged. Precisely include cleaned modules, helpers and executable fixtures
in strict Pyrefly. Preserve independent commands/reports, refusal reasons and
causes, markers, Given/When/Then, and concise truthful slice docstrings.
Retain all 13 command and 16 declaration cases (8+5 and 4+8+4), with historical
marker identities intact.

- **AC-1 TODO** Given disposable Work/test/example arrangements, command rules
  select the declared scope and reject invalid inputs precisely; static checks
  report declarations without claiming execution, coverage or completion.

  Validation: review import isolation, named fixtures and literal expectations;
  run marked cases, affected Make tests, strict typing, lint/format, doc/ac and
  latest CI.
