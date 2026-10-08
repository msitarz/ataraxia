# Rolling-window outcomes

After Bar delivery, own new `test/ataraxia/unit/test_rolling_window.py` and its
strict include. Move only `test_rolling_window_runner` and `test_rolling_window`
from `test_feature.py`; leave SMA cases untouched. Precisely type local
hand-written node/runner collaborators and their dependency contracts.

Preserve the runner sequence 3,4,5 at maxlen 2 with complete tuples `(3,)`,
`(4,3)`, `(5,4)`, and the node's supplied dependency identity. Exercise the
public node factory's actual runner and fresh state, with literal tuples. Cover
empty initial state and zero-valued input without properties, subprocesses or a
shared graph-fixture framework. Keep setup here; compute lifecycle is deferred.

- **AC-1 TODO** Given typed local inputs and node construction, real rolling
  runners preserve warm-up/newest-first ordering, capacity and fresh state,
  including zero items, with the supplied node dependency unchanged.

  Validation: compare migrated case inventory and complete tuples; run the new
  module and legacy SMA remainder, and the values group's required checks.
