# Rule owners

Place engineering, ADR, documentation, contribution, and delivery rules in
focused owning documents. Keep current architecture separate from proposed
changes. Link to an owner instead of repeating prose in work-unit READMEs.
Engineering guidance retains structural review of overlapping types and fields,
module placement, and justified decisions to leave a sound design alone.

Use `08fcd28` as a structural reference, then adapt only rules appropriate to
the master-based v2 workflow.
The existing feat workflow owns legacy delivery rules; its replacement is a
separate unit. These children move rules still stranded in `AGENTS.md`.

## Work units

- **DONE** Engineering rules — moved repair, coding, type, structural review, and
  testing guidance to `doc/engineering.md`.
- **DONE** ADR rules — moved eligibility, format, amendments, and writing
  guidance to `doc/adr-workflow.md`.
- **DONE** Architecture contracts — moved the repository map and current
  computation and backtesting contracts to `doc/architecture.md`.
- **TODO** [Contribution rules](contribution/README.md)
- **TODO** [Documentation ownership](documentation/README.md)
