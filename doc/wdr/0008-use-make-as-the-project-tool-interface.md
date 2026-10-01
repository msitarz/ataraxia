# 8. Use Make as the project tool interface

Date: 2026-10-01

## Status

Accepted

## Context

Agents need a predictable route for project tools and focused file checks.
Direct tool commands offer flexibility, but require callers to reproduce the
right executable, environment, and options; those invocations can diverge from
full verification defaults and Make-managed offline caches.

## Decision

Route agent and contributor invocations of project tools through Make targets.
Keep the Makefile as the executable command owner, adding a described target
when a project action lacks one. Target selectors narrow focused checks while
full verification and CI targets retain their complete defaults.

## Consequences

Project tool actions have one findable command interface, while new actions
must preserve defaults and expose focused selectors where useful. See
[agent routing](../../AGENTS.md),
[contributor guidance](../../CONTRIBUTING.md), and the
[Makefile](../../Makefile).
