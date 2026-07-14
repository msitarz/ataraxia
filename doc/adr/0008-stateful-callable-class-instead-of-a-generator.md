# 8. Stateful callable class instead of a generator

Date: 2026-07-14

## Status

Accepted

## Context

ADRs [2. strategy and features as pure functions ](0002-strategy-and-features-as-pure-functions.md), [3. feature composition](0003-feature-composition.md) and [4. compute graph](0004-compute-graph.md) introduced `ataraxia`'s compute design.  Due to the nature of features, pure functions implementing them require static parameters such as the period of a moving average.  The backtesting loop iterates over the instrument OHLCV values and dependency injection provides that value in each iteration step.  This means feature parameters must be stored in some form of a container and then fed into the pure function.

In the first design of the computable graph I used generators to keep the state of the pure function.  Generators seemed as a good fit due to their iterative nature (backtester is a loop).  This led to weird constructions such as:

```py
def sma_generator(period: int) -> Generator[SmaReturn, RollingWindowReturn]:
    bars = ()
    while True:
        bars = yield sma(tuple(b.close for b in bars), period)
```

It introduced a while loop just for the sake of keeping parameters and required generator priming before operation.  This would introduce a friction for new quants and `ataraxia`'s goal is to be transparent.  Sending values to generators and receiving in the same pass is also not intuitive and can be a source of many errors.

## Decision

Change the generator-based design to a class implementing `__call__` method.  Generators are syntactic sugar for this anyway.  This solves problem with using yield to provide and receive values, using infinite loop, and storing feature parameters similarly to how a closure works, but using infinite loop instead of nested functions.

With the new design, the generator above can be refactored to:

```py
class Sma:
    period: int

    def __call__(self, bars: RollingWindowReturn) -> SmaReturn:
        return sma(tuple(b.close for b in bars), self.period)
```

## Consequences

Less friction when working with `ataraxia`.
