# SPDX-License-Identifier: Apache-2.0
"""Typed script import setup shared by acceptance command test modules."""

from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "script"
SCRIPT = SCRIPT_DIR / "acceptance_tests.py"

# The actual Make script is flat and imports sibling modules by their top-level
# names, so expose its directory only while importing its public module.
with patch.object(sys, "path", [str(SCRIPT_DIR), *sys.path]):
    from script import acceptance_tests as acceptance_tests

# Keep the static checker available through its typed public module as well;
# it uses the same flat sibling-import layout as the command script.
with patch.object(sys, "path", [str(SCRIPT_DIR), *sys.path]):
    from script import acceptance_coverage as acceptance_coverage
