# Source instance and context forwarding

After provider failures delivery, own `test/ataraxia/unit/test_source.py`, its
three existing cases and all local Provider collaborators; add its strict
include. Retain runner item 1 and source sequence 3,4 followed by StopIteration.
Exercise public `send` and `factory`: successive sends reach the same retained
runner, repeated factory calls preserve identity, iteration retains the supplied
provider, and source dependencies remain empty under ADR 12.

Use faithful hashable, context-managed `Provider[int]` collaborators with
precise iterator, self/return, exception-type/value and TracebackType
signatures. Do not erase the contract into object/Any or suppress diagnostics.
For the retained context case, assert entering returns the same source and
forwards the actual RuntimeError object and traceback unchanged. Preserve the
existing None-traceback case; cover bool/None provider exit results as
forwarding outcomes, including the retained False result, without replacing
product source code.

- **AC-1 TODO** Given precisely typed Provider collaborators, public source
  iteration/send/factory preserve item values and provider/runner identity while
  context entry/exit forward exact arguments and supported return values.

  Validation: inspect collaborator fidelity, preserved cases and identity/error
  observations; run this module and provider modules, plus the input group's
  checks. This verifies forwarding, not real compute-generator resource closure.
