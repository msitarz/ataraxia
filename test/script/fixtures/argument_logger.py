#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Record arguments received by a disposable fake executable."""

import json
from pathlib import Path
import sys

Path("argv.json").write_text(json.dumps(sys.argv[1:]))
