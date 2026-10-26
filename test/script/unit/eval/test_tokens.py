# SPDX-License-Identifier: Apache-2.0
"""Typed token-estimation adapter and report wiring guarantees."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import pytest

from script.eval.model import (
    DirectoryOption,
    EstimateBasis,
    EstimateCompatibility,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
    TokenEstimate,
)
from script.eval.tokens import (
    TiktokenEstimator,
    TokenizerSelection,
    build_dry_run_report,
    tiktoken_estimator,
)


@dataclass(frozen=True)
class _Selection:
    encoding_name: str | None
    library_version: str | None
    tokenizer_version: str | None
    compatibility: EstimateCompatibility
    diagnostic: str | None


def _plan(instructions: bytes | None = None) -> FrozenPlan:
    configuration = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=("model-a", "model-a"),
        efforts=("low",),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=None,
    )
    prompts = (b"same prompt", b"same prompt")
    calls = tuple(
        PlannedCall(
            position=position,
            context_indices=(0,),
            model=model,
            effort="low",
            prompt_sha256=sha256(prompt).hexdigest(),
            prompt=prompt,
        )
        for position, (model, prompt) in enumerate(
            zip(configuration.models, prompts, strict=True)
        )
    )
    snapshot = (
        InstructionsSnapshot(
            repository_path="instructions.md",
            commit_blob_sha="blob",
            content_sha256=sha256(instructions).hexdigest(),
            content=instructions,
        )
        if instructions is not None
        else None
    )
    return FrozenPlan(
        run_id="run",
        configuration=configuration,
        repository_root=Path("/repo"),
        head_commit="head",
        snapshots=(),
        boundary_bytes=(),
        instructions_file=snapshot,
        calls=calls,
    )


def test_tiktoken_adapter_forwards_selected_metadata_and_exact_bytes() -> None:
    # Given
    selection = _Selection("encoding-a", "4.0", "encoding-a-v1", "approximate", None)
    selected: list[str] = []
    counted: list[tuple[bytes, TokenizerSelection]] = []

    def select(model: str) -> _Selection:
        selected.append(model)
        return selection

    def count(content: bytes, tokenizer: TokenizerSelection) -> int:
        counted.append((content, tokenizer))
        return 7

    estimator = TiktokenEstimator(select, count)

    # When
    result = estimator.estimate(
        b"\x00exact bytes", "requested-model", "supplied_context"
    )

    # Then
    assert selected == ["requested-model"]
    assert counted == [(b"\x00exact bytes", selection)]
    assert result.model == "requested-model"
    assert result.token_count == 7
    assert result.method == "tiktoken"
    assert result.library_version == "4.0"
    assert result.tokenizer_version == "encoding-a-v1"
    assert result.basis == "supplied_context"
    assert result.compatibility == "approximate"


def test_unknown_selection_is_explicit_and_does_not_count() -> None:
    # Given
    selection = _Selection(None, None, None, "unknown", "no compatible encoding")
    counted: list[bytes] = []
    estimator = TiktokenEstimator(
        lambda model: selection,
        lambda content, tokenizer: counted.append(content) or 0,
    )

    # When
    result = estimator.estimate(b"context", "unrecognized-model", "supplied_context")

    # Then
    assert result.token_count is None
    assert result.compatibility == "unknown"
    assert result.diagnostic == "no compatible encoding"
    assert result.model == "unrecognized-model"
    assert counted == []


def test_report_estimates_repeated_calls_and_instructions_separately() -> None:
    # Given
    plan = _plan(instructions=b"frozen instruction\x00")
    received: list[tuple[bytes, str, str]] = []

    class RecordingEstimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            received.append((content, model, basis))
            return TokenEstimate(
                model=model,
                token_count=len(content),
                method="injected",
                library_version=None,
                tokenizer_version=None,
                basis=basis,
                compatibility="exact",
                diagnostic=None,
            )

    estimator = RecordingEstimator()

    # When
    report = build_dry_run_report(plan, estimator)

    # Then
    assert received == [
        (b"same prompt", "model-a", "supplied_context"),
        (b"frozen instruction\x00", "model-a", "instructions_file"),
        (b"same prompt", "model-a", "supplied_context"),
        (b"frozen instruction\x00", "model-a", "instructions_file"),
    ]
    assert report.plan is plan
    assert report.scheduled_call_count == 2
    assert tuple(item.position for item in report.estimates) == (0, 1)
    assert report.estimates[0].context.token_count == len(b"same prompt")
    assert report.estimates[0].instructions_file is not None
    assert report.estimates[0].instructions_file.basis == "instructions_file"
    assert report.cli_binding_known is False
    assert report.effective_call_identities_known is False


def test_report_does_not_estimate_automatic_instructions() -> None:
    # Given
    plan = _plan()
    received: list[tuple[bytes, str, str]] = []

    class RecordingEstimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            received.append((content, model, basis))
            return TokenEstimate(
                model=model,
                token_count=1,
                method="injected",
                library_version=None,
                tokenizer_version=None,
                basis=basis,
                compatibility="exact",
                diagnostic=None,
            )

    # When
    report = build_dry_run_report(plan, RecordingEstimator())

    # Then
    assert received == [
        (b"same prompt", "model-a", "supplied_context"),
        (b"same prompt", "model-a", "supplied_context"),
    ]
    assert all(item.instructions_file is None for item in report.estimates)


def test_default_tiktoken_adapter_exposes_unfinished_package_leaf() -> None:
    # Given
    estimator = tiktoken_estimator()

    # When / Then
    with pytest.raises(NotImplementedError, match="tiktoken encoding selection"):
        estimator.estimate(b"context", "model-a", "supplied_context")
