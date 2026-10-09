# Check every rolling-window prefix against a sequence model

After adoption, own one precisely typed generated case in
`test/ataraxia/unit/test_rolling_window.py`; preserve both named tests, their
inputs and markers. Exercise the actual `RollingWindowRunner[int]` with capacity
0 through 8 and integer sequences of length 0 through 24, values -100 through
100. Create a fresh runner for every example. Explicit examples include zero
capacity, empty input, capacity one, duplicate values and length beyond
capacity.

For every nonempty input prefix, compare the complete returned tuple with an
independent ordinary-sequence model: the most recent at-most-capacity inputs in
reverse chronological order. Treat capacity zero explicitly as an empty result;
do not copy deque operations or derive expectations from the runner. Retain all
prefix observations so an ordering/truncation error at an intermediate step
cannot hide behind the final result. Use adopted 100-example in-process
settings. No helper/public API or production/type-contract changes are required.

- **AC-1 TODO** Given bounded capacities and input sequences, actual runner
  outputs at every prefix match the independent newest-first model, including
  zero-capacity and truncation boundaries, with fresh state and named cases
  preserved under precise strict typing.

  Validation: independently review the model/bounds and explicit examples; run
  the generated and both named cases through Make, inspect strict-folder
  results and preserved markers, then run doc/ac checks.
