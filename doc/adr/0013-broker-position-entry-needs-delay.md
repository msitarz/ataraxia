# 13. Broker position entry needs delay

Date: 2026-07-23

## Status

Accepted

## Context

The architecture makes it so that lookahead errors become impossible due to event-driven processing.  The purpose of the computation graph is to send signals based on processed data and then measure how those signals perform by implementing a broker that accounts for positions and orders.

Say that the signal is issued at a bar at t=0 with a market order, as well as stop loss and take profit orders.  It is then impossible in a real-case scenario to execute any order at t=0.  The earliest possible scenario is to execute it at t=1.  In the real world that is often not possible anyway and a longer delay is needed, as well as accounting for slippage, spread, partial fills, etc.

## Decision

Broker implementations must make sure that they delay order executions when receiving a signal.

A most naive implementation might enter at the close of the bar that issued a signal at t=0, but quants must understand that this is an overly simplified version that produces unrealistic results.

## Consequences

Broker implementation becomes a point of potential error if the forced delay of at least one bar in order execution after receiving the signal is not taken into account.
