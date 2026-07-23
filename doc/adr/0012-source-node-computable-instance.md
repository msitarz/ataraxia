# 12. Source node computable instance

Date: 2026-07-23

## Status

Accepted

## Context

Source nodes are different from other computable nodes as their instances are passed through other computable nodes as dependencies down the graph.

This means that I cannot simply create new instances of source nodes within the computable nodes when returning its dependencies.  That would result in their hashes being different for seemingly the same input data and the graph will not compute as it should.

## Decision

Each computable node that needs data from the source will accept a source node instance via dependency injection and pass it down further in the computable graph.

This is the same for source node runner and provider instances.  Source node keep their instances without instatiating then anew, meaning that both need to be kept as source node attributes.

## Consequences

The trade-off here was to make the compute loop more complex by handling special cases for source nodes and injecting data from the provider there, or to make the source computable node a bit more complex to pass through data yielded from the provider into the source node runner.

The latter choice makes the computation design coherent, so I opted for that one.
