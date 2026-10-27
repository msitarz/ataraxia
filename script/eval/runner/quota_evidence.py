# SPDX-License-Identifier: Apache-2.0
"""Carry probe evidence alongside original raised exceptions."""

from script.eval.model import QuotaProbeEvidence, QuotaProbeRequest

_EVIDENCE_ATTRIBUTE = "_ataraxia_quota_probe_evidence"


def attach_quota_probe_evidence(
    error: BaseException, evidence: QuotaProbeEvidence, /
) -> None:
    """Attach evidence without replacing the original exception or prior facts.

    The private exception attribute stores an immutable tuple so repeated
    probes that encounter the same exception object do not overwrite one
    another. Attachment failure is best-effort and never masks ``error``.
    """
    try:
        attributes = vars(error)
        stored = attributes.get(_EVIDENCE_ATTRIBUTE, ())
        if not isinstance(stored, tuple) or not all(
            isinstance(item, QuotaProbeEvidence) for item in stored
        ):
            return
        if any(item.request is evidence.request for item in stored):
            return
        attributes[_EVIDENCE_ATTRIBUTE] = (*stored, evidence)
    except Exception:
        return


def quota_probe_evidence(
    error: BaseException, request: QuotaProbeRequest, /
) -> QuotaProbeEvidence | None:
    """Find evidence only for the exact request object held by the caller.

    Callers retain the original ``QuotaProbeRequest`` across ``poll``. A missing
    match means incomplete evidence; it never implies probe success.

    Returns:
        Evidence associated with this exact request object, if retained.
    """
    try:
        stored = vars(error).get(_EVIDENCE_ATTRIBUTE)
    except Exception:
        return None
    if not isinstance(stored, tuple):
        return None
    for item in stored:
        if isinstance(item, QuotaProbeEvidence) and item.request is request:
            return item
    return None
