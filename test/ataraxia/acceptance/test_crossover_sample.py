# SPDX-License-Identifier: Apache-2.0
"""User-visible refusal effects for malformed sample runs."""

from dataclasses import dataclass
from pathlib import Path
import shutil

import pytest

from test.ataraxia.cli_process import CliResult, run_cli

PREVIOUS_OUTPUT = b'{"previous": "result"}\n'


@dataclass(frozen=True)
class FailureCase:
    """One malformed shard and one complete pre-existing-output arrangement."""

    case_id: str
    csv_contents: str | None
    reason: str
    previous_output: bytes | None


@dataclass(frozen=True)
class FailurePaths:
    """Copied process inputs and their byte snapshots for one refusal case."""

    strategy: Path
    shards: Path
    shard: Path | None
    output: Path
    inputs: tuple[Path, ...]
    input_bytes: tuple[bytes, ...]


FAILURE_CASES = (
    FailureCase("False-no-shards", None, "No backtest completed", None),
    FailureCase("False-empty-file", "", "CSV file must contain a header", None),
    FailureCase(
        "False-header-only",
        "timestamp,open,high,low,close,volume\n",
        "contains no bars",
        None,
    ),
    FailureCase(
        "False-bad-header", "wrong,header\n", "CSV file must contain a header", None
    ),
    FailureCase(
        "False-bad-value",
        "timestamp,open,high,low,close,volume\n"
        "1,100,200,50,150,1\n2,invalid,200,50,150,1\n",
        "Invalid bar",
        None,
    ),
    FailureCase(
        "False-short-row",
        "timestamp,open,high,low,close,volume\n1,100\n",
        "Invalid bar",
        None,
    ),
    FailureCase("True-no-shards", None, "No backtest completed", PREVIOUS_OUTPUT),
    FailureCase(
        "True-empty-file", "", "CSV file must contain a header", PREVIOUS_OUTPUT
    ),
    FailureCase(
        "True-header-only",
        "timestamp,open,high,low,close,volume\n",
        "contains no bars",
        PREVIOUS_OUTPUT,
    ),
    FailureCase(
        "True-bad-header",
        "wrong,header\n",
        "CSV file must contain a header",
        PREVIOUS_OUTPUT,
    ),
    FailureCase(
        "True-bad-value",
        "timestamp,open,high,low,close,volume\n"
        "1,100,200,50,150,1\n2,invalid,200,50,150,1\n",
        "Invalid bar",
        PREVIOUS_OUTPUT,
    ),
    FailureCase(
        "True-short-row",
        "timestamp,open,high,low,close,volume\n1,100\n",
        "Invalid bar",
        PREVIOUS_OUTPUT,
    ),
)


def arrange_failure_case(
    tmp_path: Path, project: Path, case: FailureCase
) -> FailurePaths:
    """Copy the shipped strategy and write this case's exact disposable inputs."""
    strategy = tmp_path / "example" / "crossover.py"
    strategy.parent.mkdir()
    shutil.copyfile(project / "example" / "crossover.py", strategy)

    shards = tmp_path / "shards"
    shards.mkdir()
    shard = None
    if case.csv_contents is not None:
        shard = shards / "invalid.csv"
        shard.write_text(case.csv_contents, encoding="utf-8")

    output = tmp_path / "output.json"
    if case.previous_output is not None:
        output.write_bytes(case.previous_output)

    inputs = (strategy,) if shard is None else (strategy, shard)
    return FailurePaths(
        strategy=strategy,
        shards=shards,
        shard=shard,
        output=output,
        inputs=inputs,
        input_bytes=tuple(path.read_bytes() for path in inputs),
    )


def assert_failure_state(
    result: CliResult, paths: FailurePaths, case: FailureCase
) -> None:
    """Check the refusal, offending input, preserved bytes, and output state."""
    assert result.exit_code == 1
    assert result.stdout == ""
    assert case.reason in result.stderr
    if paths.shard is not None:
        assert str(paths.shard) in result.stderr
    if case.previous_output is None:
        assert not paths.output.exists()
    else:
        assert paths.output.read_bytes() == case.previous_output
    expected_shards = () if paths.shard is None else (paths.shard,)
    assert set(paths.shards.iterdir()) == set(expected_shards)
    assert tuple(path.read_bytes() for path in paths.inputs) == paths.input_bytes


@pytest.mark.parametrize(
    "case", FAILURE_CASES, ids=[case.case_id for case in FAILURE_CASES]
)
@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/failures/README.md",
    ac="AC-1",
)
def test_cli_shard_failure_preserves_output(tmp_path: Path, case: FailureCase) -> None:
    """Checks refusal effects and preserves absent or pre-existing output state."""
    # Given
    project = Path(__file__).resolve().parents[3]
    paths = arrange_failure_case(tmp_path, project, case)

    # When
    result = run_cli(
        ["-s", paths.strategy, "-d", paths.shards, "-o", paths.output],
        cwd=tmp_path,
        project=project,
        state=tmp_path / "process-state",
    )

    # Then
    assert_failure_state(result, paths, case)


@pytest.mark.covers(
    work="doc/feat/testing-conformance/ataraxia/cli/failures/README.md",
    ac="AC-1",
)
def test_main_print_error_and_exit(tmp_path: Path) -> None:
    """Checks the empty-directory refusal and omitted-output default."""
    # Given
    project = Path(__file__).resolve().parents[3]
    strategy_source = project / "example" / "crossover.py"
    strategy = tmp_path / "showcase.py"
    shutil.copyfile(strategy_source, strategy)
    sample_directory = tmp_path / "samples"
    sample_directory.mkdir()
    strategy_bytes = strategy.read_bytes()

    # When
    result = run_cli(
        ["--sink", strategy.name, "--shards-dir", sample_directory.name],
        cwd=tmp_path,
        project=project,
        state=tmp_path / "process-state",
    )

    # Then
    assert result.exit_code == 1
    assert result.stdout == ""
    assert result.stderr == "No backtest completed, check params and output file\n"
    assert not (tmp_path / "results.json").exists()
    assert tuple(sample_directory.iterdir()) == ()
    assert strategy.read_bytes() == strategy_bytes
