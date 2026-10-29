#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Controlled executable for standalone harness tests."""

import os
import sys
import time

if sys.argv[1:] == ["--version"]:
    sys.stdout.write("fake codex 1\n")
    raise SystemExit(0)
if os.environ.get("FAKE_READY_FIFO"):
    with open(os.environ["FAKE_READY_FIFO"], "w") as ready:
        ready.write("ready\n")
    time.sleep(30)
sys.stdout.write('{"type":"turn.completed"}\n')
raise SystemExit(int(os.environ.get("FAKE_EXIT", "0")))
