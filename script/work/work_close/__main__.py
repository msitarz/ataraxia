# SPDX-License-Identifier: Apache-2.0
"""Run the command with ``python -m script.work.work_close``.

API:
* ``python -m script.work.work_close`` invokes the closure planning command.

Connections:
* The entry point delegates to ``cli.main`` and exits with its return code.
"""

from script.work.work_close.cli import main

raise SystemExit(main())
