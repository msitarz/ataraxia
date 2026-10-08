# Residual Bar conformance

Own `test/ataraxia/unit/test_bar.py`, including its local `data` fixture. Keep
the already delivered strict include and typed mapping contract; this is no
second typing pilot. Precisely annotate remaining tests and use Given/When/Then.

Replace private `_normalize` probes with `Bar.from_map` arrangements preserving
integer normalization, quarter-point conversion and the `3.2 -> 13` rounding
regression. Compare complete literal Bars: the existing mapping yields timestamp
1234, prices 41/122/40/103 and volume 4321. Do not compute expected prices with
the production conversion formula. Parametrize `within` below/at/inside/at/above
the existing 5..20 range, preserving the interior 14 case and inclusive edges.
Add no instrument, malformed-input or normalization policy.

- **AC-1 TODO** Given the retained mapping/rounding and range cases, public Bar
  construction and `within` produce complete literal normalized values and
  inclusive-boundary outcomes without losing the strict pilot's contract.

  Validation: review preserved case identities, public boundaries and
  independent literals; run the module and the values group's required checks.
