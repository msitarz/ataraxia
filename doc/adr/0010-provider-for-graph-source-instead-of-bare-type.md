# 10. Provider for graph source instead of bare type

Date: 2026-07-15

## Status

Accepted

Amended by [11. Multi-source single-sink DAG](0011-multi-source-single-sink-dag.md)

## Context

The current implementation allows for bare type to supply the computable graph with initial data.  The only bare supported type is `Bar` for now, yet the typing for the dependency is poining users in the wrong direction, indicating that all types are supported.

## Decision

Introduce `Provider` concept which will act as data input for the computable graph.  At first, it can be just a stub with a single `BarProvider`, but with the passage of time, the graph implementation can grow to support multiple data sources.

## Consequences

Reduce ambiguity by introducing concrete concept for data input into the graph.
