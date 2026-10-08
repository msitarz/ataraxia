# Acceptance command construction

Extract only the eight `build_command` cases from legacy
`test_acceptance_tests.py` into a cohesive typed module: two complete commands,
five invalid Work paths, one invalid criterion. Preserve both roots, filtering,
exact refusals and markers; add this Work's AC-1 marker. Own the command-script
import and typed temporary-root setup for the following summary leaf. Strictly
include only owned modules/helpers, not the legacy file's remaining cases. Call
the real function; justify and scope root/import setup.

- **AC-1 DONE** Given temporary owning files, command construction returns
  complete argv for valid actions and rejects missing, malformed, escaping, or
  absent Work paths and invalid criterion IDs with the defined reasons.

  Validation: review argv literals and temporary boundaries; run marked cases,
  strict typing, lint/format and doc/ac checks.
