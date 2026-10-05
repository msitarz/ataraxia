#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stand in for external uv at the registry process boundary."""

import json
import os
from pathlib import Path
import sys

Path("argv.json").write_text(json.dumps(sys.argv[1:]))
if os.environ["UV_PROXY_MODE"] == "delegate":
    os.execv(sys.executable, [sys.executable, *sys.argv[3:]])
sys.exit(0)
