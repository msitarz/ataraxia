# 16. Source manages its own provider lifecycle

Date: 2026-07-28

## Status

Accepted

## Context

backtest.py currently opens BarProvider as a context manager and wraps the full
compute call inside it. This only works because `tuple(compute(sink_node))`
fully drains the generator before the `with` block exits. That's correctness by
convention. It depends on every caller remembering to drain the generator while
still inside the `with`. Stream results later instead of collecting to a tuple,
and the provider closes before the generator is done, since generators are lazy
and the `with` block's `__exit__` has no idea whether the generator was actually
consumed.

It is the same failure category as the look-ahead bias bug in ADR-13. It is
better to have correctness by construction, not by caller discipline.

## Decision

`Source` protocol gets `__enter__`/`__exit__`. `SourceNode` delegates straight
to its provider. `compute()` wraps its loop in `with source:`.

Move the `Provider` protocol out of the `compute/protocol.py` and into
`provider.py`. Compute packages becomes unaware of I/O.

Since `compute()` is a generator, that `with` block's `__exit__` runs on normal
exhaustion, on an exception propagating out, and on `GeneratorExit` when the
generator is closed or garbage collected mid-iteration. The provider closes
exactly when the generator's lifetime ends, no matter how the caller consumes
it, eager tuple, stream, or early abandonment.

backtest.py drops its own `with` block. Ownership moves entirely into
`compute()`.

## Consequences

- Every `Source` implementation now carries `__enter__`/`__exit__`.
- The entire compute package is trading-concepts and I/O agnostic providing
  clear design boundaries.
- Multi-source, when it lands, needs `ExitStack` semantics to enter and exit N
  providers with correct partial-failure cleanup. That complexity now has
  exactly one place to live: `compute()`. The whole computable graph computation
  code is colocated.
