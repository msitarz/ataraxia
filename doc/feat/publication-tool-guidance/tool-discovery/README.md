# Make target discovery

Clarify the startup route in `AGENTS.md` and its owner in
`CONTRIBUTING.md`: consult `make help` when the target is unfamiliar, current
target knowledge is missing, or the Make interface may have changed. Reuse
known current targets across turns; recheck when uncertain or after an
interface change. This is a project-tool discovery step, not a prerequisite
for Git or GitHub commands.

Keep all project tool invocations behind Make. Preserve the existing rule to
add or extend a described target when a required project invocation is absent.
Keep the route concise and consistent between startup and contributor
guidance. Preserve WDR 8's Make-interface policy; add no automation or new WDR
unless implementation reveals a consequential decision beyond clarification.

- **AC-1 TODO** Given a known current Make target or missing target knowledge,
  the startup and contributor routes state when to consult `make help`, keep
  project commands on Make, and preserve the missing-target rule without
  requiring unrelated Git or GitHub discovery.

  Validation: manually trace both reading routes against the Make interface
  policy and confirm their triggers and owner agree.
