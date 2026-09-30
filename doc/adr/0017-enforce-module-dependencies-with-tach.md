# 17. Enforce module dependencies with Tach

Date: 2026-09-28

## Status

Accepted

## Context

[ADR 16](0016-source-manages-its-own-provider-lifecycle.md) keeps the
computation engine independent of trading concepts and concrete I/O. An import
of `provider` or `broker` into `compute/` could violate that boundary while
behavior tests and type checking still pass. Reviewing every import manually
leaves the boundary dependent on convention.

## Decision

Use Tach to check the module dependencies declared in the root `tach.toml`.
Run `tach check` and `tach check-external` through `make arch-check`, included
in `make ci-check` and `make ci`. Use Tach instead of maintaining a custom AST
checker in architecture tests.

Keep explicit dependency lists for the application modules. `compute/` may
depend only on its own modules and shared errors. Shared errors have no internal
dependencies. Neither may import third-party packages. Errors and utilities
aren't Tach utility modules: callers must declare dependencies on them
explicitly. Check function-local and `TYPE_CHECKING` imports, and reject
dependencies on undeclared project modules.

This enforces the existing boundary; it doesn't change ADR 16's resource
ownership or module responsibilities. Don't add separate checks for
standard-library imports or built-in I/O calls.

## Consequences

CI rejects prohibited module imports. Adding a module or changing its
dependencies requires reviewing `tach.toml`. Tach is an additional development
dependency, but the project doesn't maintain its own import checker.
Standard-library imports, built-in I/O calls, and dynamically constructed
imports still need code review.
