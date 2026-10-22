# Try representative Works

## Purpose

Use two or three Works to assess the guidance and decide the next adjustment.

**Status: ABORT.** The maintainer stopped this Work before the trial. The
required cases, observations, reading-route walkthrough, and next-decision
record were not completed; the acceptance criteria remain `TODO`.

## Goals

- Check that the combined route is usable before adding more process.
- Preserve observations and uncertainty that the maintainer can inspect.

## Inherited constraints

Apply the [parent constraints](../README.md#inherited-constraints).

## Non-Goals

- Authorize unrelated product implementation or claim measured efficiency gains.
- Add benchmarks, review infrastructure, or cleanup replacement design.

## Acceptance criteria

### **AC-1 TODO** Concrete cases reveal guidance fit and remaining friction

A retained record identifies two or three concrete Works and explains why they
exercise different relevant decisions. Together the cases cover a coherent leaf,
uncertain decomposition with retained exploration, inherited guarantees and
composition, progressive evidence, and focused review or a bounded repair
decision. At least one case is a real Work delivery that uses the combined
guidance and retains evidence of applicable architecture, wiring, testing,
implementation, and review. Progression is proportional to the change; a simple
change does not acquire unnecessary stages just to satisfy the trial. Remaining
cases may use existing Works, new guidance-defined contracts, or walkthroughs
with explicit evidence limits; walkthroughs alone cannot satisfy this criterion.

This is a future acceptance requirement. The trial uses an independently
authorized Work delivery; defining this trial does not authorize unrelated
product implementation now or later.

Observations distinguish a contract review or walkthrough from actual
implementation and runtime evidence. They record consequential ambiguity,
missing context, excessive process, and unresolved questions without claiming
unmeasured speed or quality gains. The five-minute intent target never justifies
omitting consequential detail or disguising an incoherent or unbounded outcome.

### **AC-2 TODO** Reading routes agree on the delivered guidance

A reading-route walkthrough verifies that task routes, Make reminders,
contributor guidance, role guidance, and authoritative owners agree on the
delivered rules. Conflicting pending workflow trial contracts are explicitly
reconciled or marked as superseded plans without deleting retained records or
declaring their unobserved outcomes complete.

### **AC-3 TODO** Observed cases support a bounded next decision

The retained record proposes only corrections supported by the cases and gives
the maintainer a concrete decision to retain the guidance, make a bounded
correction, or investigate a remaining question. Further tuning requires that
decision rather than an open-ended trial mandate.

## Dependencies

- DONE [Guide focused engineering review](../focused-review/README.md): make
  focused review produce supported findings and bounded repair.

## Links

- The retired workflow parent, trial preparation, trial contract, and live
  trial remain available in the
  [immutable repository history](https://github.com/msitarz/ataraxia/tree/2405ded5e1fb993c9411e77a73111b1d95f1bf2c/doc/feat/reviewable-workflow-v2).
  Their pending plans do not authorize or constrain this trial.
- [Task routes](../../../../AGENTS.md) and
  [documentation ownership](../../../README.md): discoverability and consistency
  owners.

## Additional context

This is a bounded usability trial. It does not inherit the retired workflow's
prerequisites or performance claims.
