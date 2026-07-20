# 11. Multi-source single-sink DAG

Date: 2026-07-19

## Status

Accepted

Amends [10. Provider for graph leafs instead of bare type](0010-provider-for-graph-leafs-instead-of-bare-type.md)

## Context

The shape of the dependency graph while including concepts like Providers from ADR 10. is now clear.  It is a multiple-source single-sink directed acyclic graph.  Strategy is the sink and direction of the edges points outward of the strategy to features that the strategy depends on and so on with features depending on other features.  The graph node which doesn't depend on anything is a source node.  There can be multiple source nodes (e.g. NQ, ES).

## Decision

Introduce the Source protocol and the Sink protocol for the respective node types.  Source protocol will enable input passthrough from the data shard, while sink protocol will enable discovery of all the sources to iterate over (shards) in the compute loop.

## Consequences

It enables multi-source processing to build features based on many instruments.  It completes the graph design, yet it will introduce major consequences for loop iteration logic, like being able to iterate over sources with differing timeframes.
