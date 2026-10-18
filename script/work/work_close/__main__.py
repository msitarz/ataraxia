# SPDX-License-Identifier: Apache-2.0
"""Support command invocation with ``python -m script.work.work_close``.

The module delegates to ``cli.main`` and exits with its return code, so module
invocation uses the same argument, output, and error handling as direct
command invocation.
"""

from script.work.work_close.cli import main

raise SystemExit(main())
