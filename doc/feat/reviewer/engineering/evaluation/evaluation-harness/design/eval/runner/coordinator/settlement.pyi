# SPDX-License-Identifier: Apache-2.0
"""Retained writes, durable wait closure, and cancellation precedence.

The run owner retains each submitted operation until it settles even through
repeated cancellation. A durable wait start must have a durable end and a
retained WaitRecord. A recording failure marks the run incomplete and remains
available as the cause of the primary cancellation. Probe timeout translation
must recover exact-request evidence from the exception chain before settlement.
"""
