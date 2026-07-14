# 4. Compute graph

Date: 2026-07-14

## Status

Accepted

## Context

Due to [ADR 2](0002-strategy-and-features-as-pure-functions.md) and [ADR 3](0003-feature-composition.md), strategies and features need to be represented in a way that allows injecting values returned by features into the strategies and features that depend upon them, while keeping them as pure functions.  Each feature can depend upon multiple features.

Note that currently there is no distinction between features and strategies on the conceptual level.

Looking at the requirements, we see that the entire structure represents a dependency graph for pure functions.  The input into that graph (its leaf) will be currently processed bar (OHLCV) data from some instrument.

## Decision

I need to create a compute graph where dependencies are mapped for each feature or strategy representing a graph's node. At the start of the processing will be the current processed bar from the instrument.

## Consequences

Dependency injection ensures that if multiple features need the same dependency, that value will be computed only once.

Dependency injection mechanism makes `ataraxia` more transparent to the quant.  It offloads the manual wiring process that is notes in [2. Strategy and features as pure functions](0002-strategy-and-features-as-pure-functions.md).
