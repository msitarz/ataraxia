# SMA calculation outcomes

After rolling delivery, own the seven remaining `test_sma*` functions and local
arrangements in `test/ataraxia/unit/test_feature.py`, adding its strict include.
Preserve the four parametrized missing-value placements, incomplete input,
excess-value error, missing-before-excess precedence, and zero-valued mean.
Assert literal `5`, `1`, `None`, and the exact FeatureError reason as
applicable.

Replace `test_sma_runner`'s internal `sma` patch with actual `SmaRunner` calls:
the existing one-bar/period-3 arrangement returns None; complete typed Bars
produce an independently derived close mean. Include zero close and warm-up,
with no mocked product calculation or oracle obtained by calling `sma`.
Keep fixtures local and precisely typed; do not adopt properties or add a
different moving-average/invalid-period policy.

- **AC-1 DONE** Given retained scalar/missing-value cases and real Bars, SMA and
  its runner return literal warm-up/zero/complete outcomes and preserve the
  excess-value failure and missing-value precedence without internal doubles.

  Validation: inspect the retained inputs and hand-derived close expectations;
  run the module and rolling consumers, plus the values group's required checks.
