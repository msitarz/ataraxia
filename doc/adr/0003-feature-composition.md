# 3. Feature composition

Date: 2026-07-14

## Status

Accepted

## Context

Features can depend on each other.  Bollinger Bands needs moving average.  Custom trend feature could be needed that simply returns UP, DOWN, FLAT and would be implemented depending upon moving averages.

As it should be easy to write features as pure functions ([ADR 2](0002-strategy-and-features-as-pure-functions.md)), writing code to wire up all the dependencies would quickly become an issue where quants would spend time on making `ataraxia` work rather than focusing on their strategies.

## Decision

Design the system in a way that allows for injecting return values from other features into another features.  This means we need a dependency injection system.

Features composition fits nicely into [ADR 2](0002-strategy-and-features-as-pure-functions.md) pure functions decision, allowing for functional programming thinking within `ataraxia`.

## Consequences

Need to incorporate dependency injection into the system design.
