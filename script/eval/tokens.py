# SPDX-License-Identifier: Apache-2.0
"""Provider-neutral token-estimation wiring for frozen evaluation plans.

The port consumes exact prompt bytes and a requested model. The selected
``tiktoken`` adapter is kept behind that port; its package integration and
model-to-encoding policy are deliberately unfinished in this wiring increment.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from script.eval.model import (
    CallEstimate,
    DryRunReport,
    EstimateBasis,
    EstimateCompatibility,
    FrozenPlan,
    TokenEstimate,
)


class TokenEstimator(Protocol):
    """Estimate supplied bytes without dispatching a model call.

    Implementations return explicit unknown results when they cannot establish
    an estimate. They must not silently substitute another model's tokenizer.
    """

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        """Return an estimate labeled with its input basis and method."""


@dataclass(frozen=True)
class TokenizerSelection:
    """Immutable metadata selected before token counting.

    The value is generic to the adapter boundary; it does not define how a
    provider maps model names to tokenizers. ``encoding_name=None`` means the
    adapter cannot provide a count.

    Example:
        ``TokenizerSelection("encoding-a", "4.x", "a-1", "approximate",
        None)`` identifies the selected encoding independently of the library
        and tokenizer versions. A provider-neutral estimator can use a
        different identifier such as ``"vocab-b"``.
    """

    encoding_name: str | None
    library_version: str | None
    tokenizer_version: str | None
    compatibility: EstimateCompatibility
    diagnostic: str | None


type SelectTokenizer = Callable[[str], TokenizerSelection]
type CountTokens = Callable[[bytes, TokenizerSelection], int]


class TiktokenEstimator:
    """Adapter seam for a future ``tiktoken`` backed estimator.

    Tokenizer selection and counting are injected leaf operations so wiring can
    be reviewed before the dependency, model mapping, or library behavior is
    added. A selection without an encoding returns a labeled unknown estimate.
    Exceptions from either leaf operation propagate to the caller.
    """

    def __init__(
        self,
        select_tokenizer: SelectTokenizer,
        count_tokens: CountTokens,
        /,
    ) -> None:
        """Store the adapter's tokenizer selection and counting operations."""
        self._select_tokenizer = select_tokenizer
        self._count_tokens = count_tokens

    def estimate(
        self, content: bytes, model: str, basis: EstimateBasis, /
    ) -> TokenEstimate:
        """Estimate bytes using the selected encoding, preserving its metadata.

        The selector owns model compatibility. An explicit unknown selection
        performs no counting and has ``token_count=None``.

        Returns:
            An estimate carrying the selected method, basis, and metadata.
        """
        selection = self._select_tokenizer(model)
        token_count = (
            self._count_tokens(content, selection)
            if selection.encoding_name is not None
            else None
        )
        return TokenEstimate(
            model=model,
            token_count=token_count,
            method=(
                f"tiktoken:{selection.encoding_name}"
                if selection.encoding_name is not None
                else "tiktoken"
            ),
            library_version=selection.library_version,
            tokenizer_version=selection.tokenizer_version,
            basis=basis,
            compatibility=selection.compatibility,
            diagnostic=selection.diagnostic,
        )


def tiktoken_estimator() -> TiktokenEstimator:
    """Compose the planned adapter with its unfinished package leaves.

    The returned value establishes the future composition boundary. Calling
    ``estimate`` currently raises from the private selection leaf until the
    concrete library implementation is delivered.

    Returns:
        An adapter connected to the unfinished default package leaves.
    """
    return TiktokenEstimator(_select_tiktoken_encoding, _count_tiktoken_tokens)


def build_dry_run_report(
    plan: FrozenPlan, estimator: TokenEstimator, /
) -> DryRunReport:
    """Estimate each scheduled call from its frozen context and instructions.

    Every scheduled position is retained, including repeated calls with the
    same bytes. A configured instructions file is estimated separately for
    each call's requested model. When it is absent, no estimate is fabricated
    for Codex's unavailable automatic system instructions.

    Example:
        A plan with two calls produces two ``CallEstimate`` records in position
        order. Each context estimate uses that call's exact ``prompt`` bytes;
        if the plan has an instruction snapshot, its bytes receive a separate
        ``instructions_file`` estimate. CLI binding and effective call
        identities remain unknown during dry run.

    Returns:
        A report containing the plan and one estimate record per call.
    """
    estimates = tuple(
        CallEstimate(
            position=call.position,
            context=estimator.estimate(call.prompt, call.model, "supplied_context"),
            instructions_file=(
                estimator.estimate(
                    plan.instructions_file.content,
                    call.model,
                    "instructions_file",
                )
                if plan.instructions_file is not None
                else None
            ),
        )
        for call in plan.calls
    )
    return DryRunReport(
        plan=plan,
        scheduled_call_count=len(plan.calls),
        estimates=estimates,
        cli_binding_known=False,
        effective_call_identities_known=False,
    )


def _select_tiktoken_encoding(model: str, /) -> TokenizerSelection:
    """Unfinished package leaf; model compatibility policy is unimplemented.

    Raises:
        NotImplementedError: The concrete tiktoken adapter is not implemented.
    """
    raise NotImplementedError("tiktoken encoding selection is not implemented")


def _count_tiktoken_tokens(content: bytes, selection: TokenizerSelection, /) -> int:
    """Unfinished package leaf; actual token counting is unimplemented.

    Raises:
        NotImplementedError: The concrete tiktoken adapter is not implemented.
    """
    raise NotImplementedError("tiktoken token counting is not implemented")
