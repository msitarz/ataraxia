# Make help

Generate the command index from descriptions beside target definitions in the
[Makefile](../../../../../Makefile), avoiding a separately maintained command
list.

## Outcome

`make` and `make help` display the same readable command index without running
project tools, installing dependencies, or requiring setup.

## Acceptance criteria

- Group supported targets into everyday commands, offline verification, and CI
  entry points identified as primarily for automation. Include `clean` and all
  supported `verify-*` targets.
- Describe actual behavior and side effects: `lint` applies fixes; `setup`
  installs dependencies and hooks; `ci` includes a network audit; `clean`
  removes the virtual environment and test caches.
- The Makefile owns executable commands and descriptions.
  [CONTRIBUTING.md](../../../../../CONTRIBUTING.md) owns validation policy and
  when checks are required. Implementation updates its Make targets
  introduction to direct humans and agents to `make help` before running
  project tools; read recipes only when details matter.
- Implementation extends the existing [AGENTS.md](../../../../../AGENTS.md)
  route to cover running project tools and link to that contribution guidance.
- Prefer supported Make targets. Direct tool invocation is allowed for targeted
  tests or diagnostics that existing targets do not expose.
- Preserve target behavior and validation policy. Do not recreate a command
  table elsewhere.
