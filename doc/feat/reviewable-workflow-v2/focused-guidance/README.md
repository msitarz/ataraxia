# Focused guidance

Give independently triggered guidance a focused owner so agents can read the
rules needed for their task without loading broader contribution or engineering
documents.

## Acceptance criteria

- Move repair and scope rules from `doc/engineering.md` to
  `doc/change-rules.md`, read for any repository change.
- Move validation policy from `CONTRIBUTING.md` to `doc/validation.md`, read
  when choosing checks or reporting validation evidence. Preserve existing
  requirements, offline fallback, and missing-evidence reporting.
- Route [AGENTS.md](../../../../AGENTS.md) directly to these owners. Keep
  running project tools routed to `make help`.
- Replace extracted prose with links in the broader documents; preserve
  existing headings where needed for incoming links. Update affected routes
  and the [documentation ownership map](../../../README.md).
- Add the ownership principle: give independently triggered guidance a focused
  owner; route directly to it, and link from broader documents without repeating
  its rules.
- Keep code-specific engineering guidance together. Change reading boundaries,
  not validation policy, tool behavior, or legacy feat-slice requirements.
- Verify links and anchors, preservation of moved rules, and the reading routes
  for a documentation change and a validation task.
