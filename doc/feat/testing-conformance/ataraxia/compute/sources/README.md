# Typed source and lifecycle arrangements

After dependency arrangements, own new `compute_source_inputs.py` and its strict
include. Define the retained integer source 1,3 and sink item+7 with precise
Source/Runner/send/factory/context signatures and retained runner identity.
Context records model exception type/value/TracebackType precisely; expose
observable open/closed state, not just callback counts. Runtime state stays out
of node equality/hash. No object-valued class dictionaries or untyped lambdas.

Also own a small temporary two-row CSV arrangement with real BarProvider and
SourceNode for the resource leaf. Keep actual integer-string Bar values and
capturable real file handles explicit. Do not create a generic fixture framework
or adopt unrelated test/source helpers. Leave legacy consumers untouched until
their owners merge.

- **AC-1 DONE** Given retained source inputs, typed faithful collaborators and
  real CSV arrangements expose precise context/state observations and stable
  runner identity before their consumers without forward dependencies.

  Validation: inspect types, input literals and state/hash separation under
  ADRs12/16; run strict/lint/doc/ac checks and legacy compatibility cases.
