# 2. Strategy and features as pure functions

Date: 2026-07-13

## Status

Accepted

## Context

Writing strategies and custom features is a complex task.

## Decision

Current quant backtesting libraries and platforms are designed via subclassing and using framework concepts.  Both features and strategies become tightly coupled to the framework.  This creates friction as quants cannot easily test strategies and features via TDD.  Moreover, wiring up all backtester components is often done manually, creating additional overhead.

With evolving strategies, quants must spend more and more time on the correctness of using the backtesting framework of their choosing, rather than on their strategy development.

Simplify strategy and features writing process by moving the problem into pure functions to enable TDD and designating them with single responsibility.

## Consequences

Design a system that will fade into the background as much as possible and that will enable TDD strategy and features development.
