# 9. Dict instead of tuple for dependency injection unpacking

Date: 2026-07-14

## Status

Accepted

## Context

In the first design of the computable graph, I used a tuple unpacking as the dependency injection mechism.  This is dangerous and inconsistent with other DI frameworks in the python ecosystem that use parameter name based injection.  The danger comes from changing the order of parameters either in the runner (pure function container) or in the dependency specification for the runner.

Using a dict doesn't eliminate all of the possible errors, buts is it is certainly harder to make one.

## Decision

Use dict unpacking instead of tuple unpacking for the dependency injection into the runner.

## Consequences

Using `ataraxia` becomes more robust and hardens against accidental ordering errors.
