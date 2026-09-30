# Make help

Use the Makefile as the command index after removing the duplicate command
tables from `CONTRIBUTING.md`. Make `make help` show every supported human-facing
target, including `clean`, with short descriptions that match the recipes.
Identify the CI-only targets as such; the CI workflow still calls Makefile
targets rather than duplicating their commands.

Keep validation policy in `CONTRIBUTING.md`. This unit changes command
discovery, not which checks are required or when they run. Completion means a
reader can find the appropriate target with `make help` and no command list
needs to be maintained in a second file.
