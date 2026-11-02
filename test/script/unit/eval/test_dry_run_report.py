# SPDX-License-Identifier: Apache-2.0
"""Presentation of frozen plans and token estimates."""

from hashlib import sha256
from pathlib import Path

from script.eval.dry_run import format_dry_run
from script.eval.model import (
    DirectoryOption,
    EstimateBasis,
    FrozenInputs,
    HarnessConfig,
    InstructionsSnapshot,
    SeparatorOption,
    SourceSnapshot,
    TokenEstimate,
)
from script.eval.plan import PurePlanBuilder
from script.eval.tokens import TokenEstimator, build_dry_run_report


def test_report_lists_every_position_and_separates_estimate_bases() -> None:
    # Given
    config = HarnessConfig(
        ordered_options=(
            DirectoryOption(position=0, path=Path("first")),
            SeparatorOption(position=1, value=r"\n--\n"),
            DirectoryOption(position=2, path=Path("second")),
        ),
        models=("known", "unknown", "known"),
        efforts=("low", "high"),
        concurrency=1,
        output_directory=None,
        dry_run=True,
        timeout_seconds=1.0,
        cleanup_timeout_seconds=1.0,
        grace_seconds=0.0,
        output_limit_bytes=0,
        instructions_file_path=Path("instructions"),
    )
    sources = tuple(
        SourceSnapshot(
            directory_position=position,
            repository_path=path,
            commit_blob_sha="blob",
            content_sha256=sha256(content).hexdigest(),
            content=content,
        )
        for position, path, content in (
            (0, "first/a long name.txt", b"a"),
            (0, "first/b.txt", b"bb"),
            (2, "second/c.txt", b"c"),
        )
    )
    instructions = InstructionsSnapshot(
        repository_path="instructions",
        commit_blob_sha="blob",
        content_sha256=sha256(b"xyz").hexdigest(),
        content=b"xyz",
    )
    plan = PurePlanBuilder("run").plan(
        FrozenInputs(Path("/repo"), "head", sources, instructions), config
    )

    class Estimator:
        def estimate(
            self, content: bytes, model: str, basis: EstimateBasis, /
        ) -> TokenEstimate:
            count = None if model == "unknown" else len(content)
            return TokenEstimate(
                model,
                count,
                "fake",
                "1",
                "vocab",
                basis,
                "unknown" if count is None else "approximate",
                "shared caveat",
            )

    # When
    result = format_dry_run(build_dry_run_report(plan, Estimator()))

    # Then
    assert "Dry run: 12 calls; no Codex calls or output directory" in result
    assert (
        "'first': 2 selected files\n  separator: '\\n--\\n'\n"
        "  'second': 1 selected files" in result
    )
    assert "Models: known, unknown, known" in result
    assert "Efforts: low, high" in result
    assert "Instructions file: 'instructions' (estimated separately)" in result
    rows = [
        line.strip()
        for line in result.splitlines()
        if line.startswith("  ") and ": model=" in line
    ]
    assert rows == [
        f"{position}: model={model} effort={effort} context tokens={count}"
        + (
            "; instructions tokens: UNKNOWN"
            if model == "unknown"
            else "; instructions tokens: 3"
        )
        for position, (model, effort, count) in enumerate([
            ("known", "low", "6"),
            ("known", "high", "6"),
            ("unknown", "low", "UNKNOWN"),
            ("unknown", "high", "UNKNOWN"),
            ("known", "low", "6"),
            ("known", "high", "6"),
            ("known", "low", "7"),
            ("known", "high", "7"),
            ("unknown", "low", "UNKNOWN"),
            ("unknown", "high", "UNKNOWN"),
            ("known", "low", "7"),
            ("known", "high", "7"),
        ])
    ]
    source_lines = [line.strip() for line in result.splitlines() if "source: " in line]
    assert source_lines == (
        ["source: 'first/a long name.txt'", "source: 'second/c.txt'"] * 6
        + ["source: 'first/b.txt'", "source: 'second/c.txt'"] * 6
    )
    assert (
        "Supplied-context known subtotal: 52 tokens across 8 known calls; 4 unknown"
        in result
    )
    assert "Supplied-context known range: 6-7 tokens per call" in result
    assert result.count("shared caveat") == 2
    assert "framing and overhead" in result

    assert_summaries(config, sources, instructions, Estimator())


def assert_summaries(
    config: HarnessConfig,
    sources: tuple[SourceSnapshot, ...],
    instructions: InstructionsSnapshot,
    estimator: TokenEstimator,
) -> None:
    """Check totals when every estimate is known or every estimate is unknown."""
    known_plan = PurePlanBuilder("known").plan(
        FrozenInputs(Path("/repo"), "head", sources, instructions),
        config.model_copy(update={"models": ("known",)}),
    )
    known_report = format_dry_run(build_dry_run_report(known_plan, estimator))
    assert (
        "Supplied-context total: 26 tokens across 4 known calls; 0 unknown"
        in known_report
    )
    unknown_plan = PurePlanBuilder("unknown").plan(
        FrozenInputs(Path("/repo"), "head", sources, instructions),
        config.model_copy(update={"models": ("unknown",)}),
    )
    unknown_report = format_dry_run(build_dry_run_report(unknown_plan, estimator))
    assert "Supplied-context total: UNKNOWN (4 unknown calls)" in unknown_report
    assert "known range" not in unknown_report
