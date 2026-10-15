# SPDX-License-Identifier: Apache-2.0
"""Typed script import setup shared by declaration checker tests."""

from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "script"
# The Make script imports siblings by their top-level names, so expose its
# directory only while importing its public module.
with patch.object(sys, "path", [str(SCRIPT_DIR), *sys.path]):
    from script import acceptance_coverage as acceptance_coverage
