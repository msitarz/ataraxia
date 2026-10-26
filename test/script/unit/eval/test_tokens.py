# SPDX-License-Identifier: Apache-2.0
"""Typed token-estimation adapter and report wiring guarantees."""

from hashlib import sha256
from pathlib import Path
from typing import Literal

import pytest

from script.eval.model import (
    CallEstimate,
    DirectoryOption,
    EstimateBasis,
    EstimateCompatibility,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
    SourceSnapshot,
    TokenEstimate,
)
from script.eval.tokens import (
    TiktokenEstimator,
    TokenEstimator,
    TokenizerSelection,
    build_dry_run_report,
    tiktoken_estimator,
)


def _plan(
    instructions: bytes | None = None,
    *,
    models: tuple[str, ...] = ("model-a", "model-a"),
    prompts: tuple[bytes, ...] = (b"same prompt", b"same prompt"),
    context_indices: tuple[int, ...] | None = None,
) -> FrozenPlan:
    instruction_path = Path("instructions.md") if instructions is not None else None
    configuration = HarnessConfig(
        ordered_options=(DirectoryOption(position=0, path=Path("context")),),
        models=models,
        efforts=("low",),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=instruction_path,
    )
    selected_indices = (
        context_indices if context_indices is not None else tuple(range(len(prompts)))
    )
    calls = tuple(
        PlannedCall(
            position=position,
            context_indices=(selected_indices[position],),
            model=model,
            effort="low",
            prompt_sha256=sha256(prompts[position]).hexdigest(),
            prompt=prompts[position],
        )
        for position, model in enumerate(configuration.models)
    )
    sources = tuple(
        SourceSnapshot(
            directory_position=0,
            repository_path=f"context/source-{index}.md",
            commit_blob_sha=f"source-blob-{index}",
            content_sha256=sha256(prompt).hexdigest(),
            content=prompt,
        )
        for index, prompt in enumerate(prompts)
    )
    instruction_snapshot = (
        InstructionsSnapshot(
            repository_path="instructions.md",
            commit_blob_sha="instructions-blob",
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
        snapshots=sources,
        boundary_bytes=(),
        instructions_file=instruction_snapshot,
        calls=calls,
    )


def _estimate(
    model: str,
    count: int | None,
    basis: EstimateBasis,
    compatibility: EstimateCompatibility,
    diagnostic: str | None = None,
) -> TokenEstimate:
    return TokenEstimate(
        model=model,
        token_count=count,
        method="injected-estimator",
        library_version="adapter-version",
        tokenizer_version="vocabulary-version",
        basis=basis,
        compatibility=compatibility,
        diagnostic=diagnostic,
    )


@pytest.mark.parametrize(
    ("encoding", "version", "expected_method"),
    [
        ("encoding-a", "same-version", "tiktoken:encoding-a"),
        ("encoding-b", "same-version", "tiktoken:encoding-b"),
    ],
    ids=["first-encoding", "second-encoding"],
)
def test_tiktoken_adapter_preserves_selected_encoding_and_metadata(
    encoding: str, version: str, expected_method: str
) -> None:
    # Given
    selection = TokenizerSelection(
        encoding, "library-version", version, "approximate", None
    )
    selected: list[str] = []
    counted: list[tuple[bytes, TokenizerSelection]] = []

    def select(model: str) -> TokenizerSelection:
        selected.append(model)
        return selection

    def count(content: bytes, tokenizer: TokenizerSelection) -> int:
        counted.append((content, tokenizer))
        return 19

    estimator = TiktokenEstimator(select, count)

    # When
    result = estimator.estimate(
        b"exact prompt bytes", "requested-model", "supplied_context"
    )

    # Then
    assert selected == ["requested-model"]
    assert counted == [(b"exact prompt bytes", selection)]
    assert result == TokenEstimate(
        model="requested-model",
        token_count=19,
        method=expected_method,
        library_version="library-version",
        tokenizer_version=version,
        basis="supplied_context",
        compatibility="approximate",
        diagnostic=None,
    )


def test_unknown_selection_is_explicit_and_does_not_count() -> None:
    # Given
    selection = TokenizerSelection(
        None, None, None, "unknown", "no compatible encoding"
    )
    counted: list[bytes] = []
    estimator = TiktokenEstimator(
        lambda model: selection,
        lambda content, tokenizer: counted.append(content) or 0,
    )

    # When
    result = estimator.estimate(b"context", "unrecognized-model", "supplied_context")

    # Then
    assert result == TokenEstimate(
        model="unrecognized-model",
        token_count=None,
        method="tiktoken",
        library_version=None,
        tokenizer_version=None,
        basis="supplied_context",
        compatibility="unknown",
        diagnostic="no compatible encoding",
    )
    assert counted == []


def test_report_preserves_explicit_unknown_from_provider_neutral_estimator() -> None:
    # Given
    plan = _plan()
    unknown = _estimate(
        "model-a", None, "supplied_context", "unknown", "estimator has no mapping"
    )
    received: list[tuple[bytes, str, EstimateBasis]] = []

    class UnknownEstimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            received.append((content, model, basis))
            return unknown

    estimator: TokenEstimator = UnknownEstimator()

    # When
    report = build_dry_run_report(plan, estimator)

    # Then
    assert report.estimates == (
        CallEstimate(position=0, context=unknown, instructions_file=None),
        CallEstimate(position=1, context=unknown, instructions_file=None),
    )
    assert all(item.context.token_count is None for item in report.estimates)
    assert all(
        item.context.diagnostic == "estimator has no mapping"
        for item in report.estimates
    )
    assert received == [
        (b"same prompt", "model-a", "supplied_context"),
        (b"same prompt", "model-a", "supplied_context"),
    ]


def test_report_estimates_frozen_instructions_separately_for_each_call() -> None:
    # Given
    plan = _plan(instructions=b"frozen instruction\x00")
    context = _estimate("model-a", 11, "supplied_context", "exact")
    instructions = _estimate("model-a", 4, "instructions_file", "approximate")
    outputs = (context, instructions, context, instructions)
    received: list[tuple[bytes, str, EstimateBasis]] = []

    class RecordingEstimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            received.append((content, model, basis))
            return outputs[len(received) - 1]

    # When
    report = build_dry_run_report(plan, RecordingEstimator())

    # Then
    assert received == [
        (b"same prompt", "model-a", "supplied_context"),
        (b"frozen instruction\x00", "model-a", "instructions_file"),
        (b"same prompt", "model-a", "supplied_context"),
        (b"frozen instruction\x00", "model-a", "instructions_file"),
    ]
    assert report.plan is plan
    assert report.scheduled_call_count == 2
    assert report.estimates == (
        CallEstimate(position=0, context=context, instructions_file=instructions),
        CallEstimate(position=1, context=context, instructions_file=instructions),
    )
    assert report.cli_binding_known is False
    assert report.effective_call_identities_known is False


def test_report_forwards_each_calls_model_and_frozen_prompt_in_order() -> None:
    # Given
    plan = _plan(
        instructions=b"shared instruction",
        models=("model-a", "model-b"),
        prompts=(b"first context", b"second context"),
        context_indices=(0, 1),
    )
    first_context = _estimate(
        "model-a", None, "supplied_context", "unknown", "first context unknown"
    )
    first_instruction = _estimate("model-a", 3, "instructions_file", "approximate")
    second_context = _estimate("model-b", 17, "supplied_context", "exact")
    second_instruction = _estimate("model-b", 5, "instructions_file", "exact")
    outputs = (
        first_context,
        first_instruction,
        second_context,
        second_instruction,
    )
    received: list[tuple[bytes, str, EstimateBasis]] = []

    class RecordingEstimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            received.append((content, model, basis))
            return outputs[len(received) - 1]

    # When
    report = build_dry_run_report(plan, RecordingEstimator())

    # Then
    assert received == [
        (b"first context", "model-a", "supplied_context"),
        (b"shared instruction", "model-a", "instructions_file"),
        (b"second context", "model-b", "supplied_context"),
        (b"shared instruction", "model-b", "instructions_file"),
    ]
    assert report.estimates == (
        CallEstimate(0, first_context, first_instruction),
        CallEstimate(1, second_context, second_instruction),
    )


@pytest.mark.parametrize(
    ("failure_site", "expected_count"),
    [("selection", 0), ("count", 1)],
    ids=["selection", "count"],
)
def test_estimator_failure_propagates_from_adapter_and_stops_following_leaf(
    failure_site: Literal["selection", "count"], expected_count: int
) -> None:
    # Given
    failure = RuntimeError(f"{failure_site} failed")
    counted: list[tuple[bytes, TokenizerSelection]] = []

    def fail_selection(model: str) -> TokenizerSelection:
        if failure_site != "selection":
            return TokenizerSelection(
                "encoding-a", "library-version", "tokenizer-version", "exact", None
            )
        raise failure

    def count(content: bytes, selection: TokenizerSelection) -> int:
        counted.append((content, selection))
        if failure_site == "count":
            raise failure
        return 1

    estimator = TiktokenEstimator(
        fail_selection,
        count,
    )

    # When
    with pytest.raises(RuntimeError) as raised:
        estimator.estimate(b"context", "model-a", "supplied_context")

    # Then
    assert raised.value is failure
    assert len(counted) == expected_count


def test_report_propagates_estimator_failure_without_processing_later_calls() -> None:
    # Given
    plan = _plan()
    failure = RuntimeError("estimate failed")
    received: list[tuple[bytes, str, EstimateBasis]] = []

    class FailingEstimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            received.append((content, model, basis))
            raise failure

    # When
    with pytest.raises(RuntimeError) as raised:
        build_dry_run_report(plan, FailingEstimator())

    # Then
    assert raised.value is failure
    assert received == [(b"same prompt", "model-a", "supplied_context")]


def test_default_tiktoken_adapter_exposes_unfinished_package_leaf() -> None:
    # Given
    estimator = tiktoken_estimator()

    # When
    with pytest.raises(NotImplementedError) as raised:
        estimator.estimate(b"context", "model-a", "supplied_context")

    # Then
    assert str(raised.value) == "tiktoken encoding selection is not implemented"
