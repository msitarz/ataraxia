# SPDX-License-Identifier: Apache-2.0
"""Exercise the Evaluation-owned B case selection against a clean Git tree."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from script.eval.inputs import GitRepositoryReader
from script.eval.plan import PurePlanBuilder
from script.reviewer_eval.context import review_context

ROOT = Path(__file__).resolve().parents[4]
CALLER = ROOT / "doc/feat/reviewer/engineering/evaluation/preparation/run_b_case.py"
spec = importlib.util.spec_from_file_location("reviewer_b_case", CALLER)
assert spec is not None and spec.loader is not None
caller = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = caller
spec.loader.exec_module(caller)


@pytest.mark.parametrize("rule", ["R1", "R3", "R4"])
def test_selected_case_keeps_full_plan_prompt_and_public_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rule: str
) -> None:
    # Given: a disposable repository containing only the public inputs.
    for directory in caller.DIRECTORIES:
        shutil.copytree(ROOT / directory, tmp_path / directory)
    target = tmp_path / caller.INSTRUCTIONS
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / caller.INSTRUCTIONS, target)
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "inputs",
        ],
        check=True,
    )
    monkeypatch.chdir(tmp_path)
    config = caller.config_for(["-m", "gpt-6-luna", "-e", "none", "-n"])
    reader = GitRepositoryReader()
    planner = PurePlanBuilder("test")
    full = planner.plan(reader.freeze(config), config)

    # When: the same planner receives the selected frozen case.
    selected = planner.plan(
        caller.CaseReader(reader, caller.RULES[rule]).freeze(config), config
    )

    # Then: exactly one call retains its public path and matching prompt bytes.
    assert len(selected.calls) == 1
    call = selected.calls[0]
    assert (
        selected.snapshots[call.context_indices[1]].repository_path
        == caller.RULES[rule]
    )
    assert call.prompt == full.calls[["R1", "R3", "R4"].index(rule)].prompt
    assert review_context(selected, call)[0] == frozenset({rule})
    assert selected.instructions_file == full.instructions_file
