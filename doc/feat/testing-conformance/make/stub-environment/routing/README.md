# Ordinary Make routing

Depends on helper. Move ordinary tool defaults/selectors, Markdown routing,
CLI argument forwarding, and lock routing into a focused typed module. Preserve
literal shell/single-quote handling, absent execution markers, option rejection,
and advisory failure propagation. Leave orchestration and creation for owners.

- **AC-1 DONE** Given ordinary targets and hostile arguments, recorded commands
  match promised routing, invalid inputs fail before tool invocation, and shell
  expressions never create marker files.

  Validation: run focused criterion-marked cases and strict typecheck; review
  precise helper/fixture inclusion, preserved covers markers, and full CI.
