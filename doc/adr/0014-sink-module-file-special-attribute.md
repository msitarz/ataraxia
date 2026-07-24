# 14. Sink module file special attribute

Date: 2026-07-24

## Status

Accepted

## Context

Ataraxia is importing strategy as an external module specified by the user.  This means that it needs a reliable way to find which class is actually the computable sink node to compute.

## Decision

Require by convention that the sink module assigns the class which ataraxia should process to the `__sink__` global variable.

## Consequences

Users must know about additional convention.
