# SPDX-License-Identifier: Apache-2.0
"""Call-local attempt settlement, retry eligibility, and cancellable backoff.

Pure transitions consume explicit policy inputs; the async owner performs effects.

Private helper signatures are intentionally left open for implementation.
"""
