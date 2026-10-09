# Observable source lifecycle and propagated errors

After sharing, own new `unit/compute/test_lifecycle.py` and its strict include.
Move exactly test_compute_closes_source_on_exhaustion, when_runner_raises and
when_generator_is_closed from test_loop.py, with precisely typed local failing
runner/sink. Use merged source arrangements; retain complete 1/8,3/10 steps and
context exception records.

Assert observable closed source state on exhaustion, RuntimeError("sink runner
failed") and explicit compute generator.close after first yield. Preserve exact
error identity/reason, RuntimeError/GeneratorExit types and real traceback
presence/forwarding; context observations do not replace the closed-state check.
Run actual compute; source collaborators implement the boundary faithfully.
Real file closure is the separate resource leaf, not claimed by these units.

- **AC-1 TODO** Given retained faithful source/failing-runner arrangements, real
  compute exhaustion, error and explicit close leave the source closed and
  preserve complete results and precise context/error propagation.

  Validation: inspect all three retained exit paths and state observations;
  run this module and legacy remainder, plus the subtree's required checks.
