# Registry testing boundaries

Plan bounded leaves before implementation for these ordered outcomes:

1. Isolate typed script-owned process/selection arrangements and actual imports
   as prerequisites sized separately from case migrations where necessary.
2. Move four CLI cases from `unit/test_registry_selection.py` to integration;
   keep selector cases unit-level. Preserve whole literal manifest, recoverable
   failure artifacts, source bytes/link targets, destination collisions and
   forbidden cache-contained destinations. Failure expectations are independent
   of captured stderr; output agreement is a separate forwarding obligation.
3. Clean selector/record contracts: accepted-record single-read behavior,
   changed/unsupported conditions, digest acceptance, declarations and reviewed
   evidence. Retain exact errors/causes and complete independent record values.
4. Clean payload contracts: package layout, complete inventory/resolver
   metadata, vendored metadata, wheel-link containment and local/environment
   rejection.

`support.py` mixes dynamic imports and process/manifest helpers; `conftest.py`
mixes untyped record/payload fixtures. The next map must allocate narrow owned
helper/fixture migrations before their consumers, splitting record and payload
tests/support as needed. No blanket fixture migration or generic framework.
Script ownership remains; shared Make registry consumers must retain literal
arguments, marker absence and missing-input behavior. No production changes.
Follow [parent typing and review obligations](../README.md).

- **AC-1 TODO** Given fresh disposable inputs, real registry CLI and unit
  selectors/validators preserve reviewed manifests, precise refusals, complete
  source/destination state and existing criterion coverage without installs.

  Validation: review independent fixtures/oracles and bounded ownership plans;
  run each leaf's marked cases, registry suite and affected Make registry cases,
  strict typing, lint/format, doc/ac checks and latest-head full CI. Review any
  filesystem read double for scoped restoration and the actual boundary proved.
