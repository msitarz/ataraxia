# SPDX-License-Identifier: Apache-2.0
"""Global pause, draining, cadence, bounds, and one awaited recovery probe.

Pure transitions consume explicit time and observations; the async owner polls.

Private helper signatures are intentionally left open for implementation.
"""
