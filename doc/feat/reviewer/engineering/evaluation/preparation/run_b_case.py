# SPDX-License-Identifier: Apache-2.0
"""Run one frozen scenario B case through the existing evaluation harness."""

import argparse
import asyncio
from dataclasses import dataclass, replace
from pathlib import Path
import sys

from script.eval.evidence import create_evidence_store
from script.eval.evidence_status import EvidenceStatus
from script.eval.inputs import RepositoryReader
from script.eval.model import (
    DirectoryOption,
    DryRunReport,
    FrozenInputs,
    HarnessConfig,
    RunRecord,
)
from script.eval.options import parse_config
from script.eval.standalone import create_composition, run_owned
from script.eval.workspace import acquire_workspace, validate_workspace_selection

ROOT = "doc/feat/reviewer/engineering/evaluation/"
INPUTS = ROOT + "inputs/"
DIRECTORIES = (INPUTS + "shared", INPUTS + "cases/B", INPUTS + "corpus")
INSTRUCTIONS = ROOT + "preparation/min.md"
RULES = {rule: INPUTS + f"cases/B/{rule.lower()}.txt" for rule in ("R1", "R3", "R4")}


@dataclass(frozen=True)
class CaseReader:
    """Select one exact case after the ordinary clean Git freeze."""

    reader: RepositoryReader
    case_path: str

    def freeze(self, config: HarnessConfig, /) -> FrozenInputs:
        """Return unchanged snapshots with only the selected B case retained.

        Raises:
            ValueError: The selected case is absent or duplicated.
        """
        inputs = self.reader.freeze(config)
        cases = tuple(
            source
            for source in inputs.sources
            if source.repository_path == self.case_path
        )
        if len(cases) != 1:
            raise ValueError("selected B case must appear exactly once")
        position = cases[0].directory_position
        return replace(
            inputs,
            sources=tuple(
                source
                for source in inputs.sources
                if source.directory_position != position
                or source.repository_path == self.case_path
            ),
        )


def config_for(arguments: list[str]) -> HarnessConfig:
    """Parse harness options with the fixed input directories and instructions.

    Returns:
        The validated single-model, single-effort configuration.

    Raises:
        ValueError: The fixed input or model configuration is changed.
    """
    prefix = [item for directory in DIRECTORIES for item in ("-d", directory)]
    config = parse_config([*prefix, "-i", INSTRUCTIONS, *arguments])
    directories = tuple(
        option.path.as_posix()
        for option in config.ordered_options
        if isinstance(option, DirectoryOption)
    )
    if directories != DIRECTORIES or len(config.ordered_options) != 3:
        raise ValueError("the B inputs and separators are fixed")
    if config.instructions_file_path != Path(INSTRUCTIONS):
        raise ValueError("the instructions file is fixed")
    if config.models != ("gpt-6-luna",) or len(config.efforts) != 1:
        raise ValueError("select gpt-6-luna and exactly one effort")
    return config


async def execute_case(
    config: HarnessConfig, status: EvidenceStatus, case_path: str
) -> DryRunReport | RunRecord:
    """Use the standalone workspace lifecycle with the case-selecting reader.

    Returns:
        The dry-run report or settled run record.
    """
    if config.dry_run:
        composition = create_composition(status)
        return await replace(
            composition, repository=CaseReader(composition.repository, case_path)
        ).execute(config)
    launch_cwd = Path.cwd().resolve()
    resolved = validate_workspace_selection(config, launch_cwd)
    async with acquire_workspace(config, resolved) as workspace:
        composition = create_composition(status, workspace.cwd, launch_cwd, resolved)
        return await replace(
            composition, repository=CaseReader(composition.repository, case_path)
        ).execute(config)


def main() -> int:
    """Run one selected rule and retain standalone signal and evidence handling.

    Returns:
        The standalone process status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rule", choices=RULES)
    args, options = parser.parse_known_args()
    config = config_for(options)
    status = EvidenceStatus(create_evidence_store)

    async def operation(
        config: HarnessConfig, status: EvidenceStatus
    ) -> DryRunReport | RunRecord:
        return await execute_case(config, status, RULES[args.rule])

    try:
        with asyncio.Runner() as runner:
            return runner.run(run_owned(config, status, operation))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
