# Engineering review

## Purpose

Integrate engineering-review evidence and a recorded granularity decision into a
usable reviewer with explicit coverage and traceable judgments.

## Goals

- Base engineering-review granularity on detection quality relative to
  resources, accepting higher token consumption when it improves review quality.
- Deliver the usable engineering reviewer after the Evaluation and owner
  decision.
- Preserve shared reviewer guarantees across evaluation, decision, and delivery.

## Non-Goals

- Deliver future review domains or change existing owner review and correction
  authority under the [shared parent](../README.md#non-goals).
- Select a strategy before evidence or create Works for implementation layers.

## Inherited constraints

All [reviewer shared constraints](../README.md#inherited-constraints) apply.
Each child verifies its own boundary; the engineering owner verifies integration
and decision-to-delivery consistency. The reviewer owner retains verification of
[mandatory non-function execution and responsibility separation](../README.md#ac-2-todo-future-domains-fit-without-function-specific-execution).

## Acceptance criteria

### **AC-7 TODO** Granularity follows representative detection evidence

The engineering owner records a granularity decision supported by the completed
[Evaluation](evaluation/README.md), without assuming whole-diff or function
scope.

The decision cites results against the predeclared protocol, considers per-rule
and adaptive granularity, and records uncertainty and limits of applicability.
An inconclusive result can select the simplest viable initial approach only
against the fallback and viability evidence declared before outcomes. Detection
quality, tokens, and latency remain separately visible; lower resource use alone
does not establish success. Evidence does not itself adopt review policy:
existing review, maintainer authority, and applicable decision gates remain.

### **AC-8 TODO** Usable delivery follows the decision and shared guarantees

A parent agent receives engineering judgments, coverage, and evidence through
the [delivered reviewer](delivery/README.md), consistent with AC-7's recorded
decision.

- Given completed Evaluation evidence and the recorded owner decision, delivery
  uses the selected granularity and discloses its supported scope and
  limitations.
- Without both prerequisites, production delivery does not proceed; a minimal
  experimental harness remains distinct from completed production behavior.
- Independent engineering integration review traces success, uncertainty, and
  incomplete runs through actual invocation, planning, execution, and reporting,
  confirming that the decision, criterion applicability, budgets, input
  identity, and owner handoff agree across boundaries.
- Child completion alone does not establish this integrated guarantee or the
  reviewer's parent-owned system guarantees.

## Children

- TODO [Engineering review evaluation](evaluation/README.md): Produce bounded,
  inspectable evidence comparing engineering-review detection and resource use
  across A/B/C strategies.
- TODO [Engineering reviewer delivery](delivery/README.md): Let a parent agent
  obtain focused engineering judgments for a change with explicit coverage and
  evidence.

## Additional context

The Evaluation is independently reviewable evidence; Delivery is independently
reviewable usable behavior. Their ordering does not require production
implementation before experimentation. The engineering owner records AC-7's
decision between them; neither the Evaluation nor its harness adopts policy. The
Evaluation's
[experimental process supervisor](evaluation/process-supervisor/README.md) is a
bounded harness child, not a production-runner decomposition. No discovery,
aggregation, function-level, or whole-diff Works are added.

Remaining typed architecture and further decomposition questions follow
[Work definition](../../../work-definition.md#decomposition-and-architectural-exploration)
and the [shared parent](../README.md#additional-context). This contract update
executes no experiment, telemetry preparation, architecture, or implementation.
