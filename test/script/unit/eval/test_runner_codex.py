# SPDX-License-Identifier: Apache-2.0
"""Codex adapter wiring through the typed runner boundaries."""

from pathlib import Path

import pytest

from script.eval.model import (
    AttemptEvidence,
    DirectoryOption,
    FrozenPlan,
    HarnessConfig,
    InstructionsSnapshot,
    PlannedCall,
    PreparedEvidence,
    RetryAssessment,
)
from script.eval.runner import CliBinding
from script.eval.runner.adapters import (
    CodexAttemptRequestBuilder,
    CodexCliBindingResolver,
    CodexOutcomeClassifier,
)
from script.process_supervisor import AttemptRequest

type BuilderInputs = tuple[
    FrozenPlan, PlannedCall, CliBinding, Path | None, HarnessConfig
]


def assert_builder_inputs(
    received: BuilderInputs,
    plan: FrozenPlan,
    call: PlannedCall,
    binding: CliBinding,
    staged_path: Path | None,
    config: HarnessConfig,
) -> None:
    """Check the exact objects forwarded by both request-building steps."""
    assert received[0] is plan
    assert received[1] is call
    assert received[2] is binding
    assert received[3] is staged_path
    assert received[4] is config


def configuration(**overrides: object) -> HarnessConfig:
    """Build a valid execution configuration with explicit limits."""
    values: dict[str, object] = {
        "ordered_options": (DirectoryOption(position=0, path=Path("context")),),
        "models": ("model-a",),
        "efforts": ("low",),
        "concurrency": 1,
        "output_directory": Path("out"),
        "dry_run": False,
        "timeout_seconds": 12.0,
        "cleanup_timeout_seconds": 5.0,
        "grace_seconds": 1.0,
        "output_limit_bytes": 4096,
        "instructions_file_path": Path("/repo/INSTRUCTIONS.md"),
    }
    values.update(overrides)
    return HarnessConfig.model_validate(values)


def plan_and_inputs(
    *, with_instructions: bool = True
) -> tuple[HarnessConfig, FrozenPlan, PlannedCall, CliBinding, PreparedEvidence]:
    """Create frozen inputs with distinct original and staged instruction paths."""
    instruction_path = Path("/repo/INSTRUCTIONS.md") if with_instructions else None
    config = configuration(instructions_file_path=instruction_path)
    call = PlannedCall(
        position=0,
        context_indices=(0,),
        model="model-a",
        effort="low",
        prompt_sha256="a" * 64,
        prompt=b"frozen prompt bytes",
    )
    plan = FrozenPlan(
        run_id="run-1",
        configuration=config,
        repository_root=Path("/repo"),
        head_commit="b" * 40,
        snapshots=(),
        boundary_bytes=(),
        instructions_file=InstructionsSnapshot(
            repository_path="INSTRUCTIONS.md",
            commit_blob_sha="c" * 40,
            content_sha256="d" * 64,
            content=b"frozen system instructions",
        )
        if with_instructions
        else None,
        calls=(call,),
    )
    binding = CliBinding(
        executable_path=Path("/bin/codex"),
        cli_version="codex version",
        runner_version="0.1.0",
        effective_settings=(("approval_policy", "never"),),
        quota_scope=None,
    )
    evidence = PreparedEvidence(
        output_directory=Path("/repo/out"),
        plan_artifact=Path("/repo/out/plan.json"),
        model_instructions_file=(
            Path("/repo/out/instructions.bin") if with_instructions else None
        ),
    )
    return config, plan, call, binding, evidence


def settled_evidence(config: HarnessConfig) -> AttemptEvidence:
    """Build one settled supervisor evidence value for classifier tests."""
    request = AttemptRequest(
        argv=("/bin/codex",),
        cwd=Path("/repo"),
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        grace_seconds=config.grace_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
    )
    return AttemptEvidence(
        control_flow="returned",
        outcome=None,
        error_type=None,
        diagnostic=None,
        request=request,
        started_at_utc="2026-10-27T00:00:00Z",
        ended_at_utc="2026-10-27T00:00:01Z",
        usage_telemetry=None,
    )


def test_binding_uses_resolved_path_for_probe_and_settings_in_order() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    executable_path = Path("/verified/codex")
    events: list[str] = []
    probed_paths: list[Path] = []
    settings_inputs: list[tuple[Path, HarnessConfig]] = []

    def resolve_executable() -> Path:
        events.append("resolve")
        return executable_path

    def probe_version(path: Path) -> str:
        events.append("version")
        probed_paths.append(path)
        return "codex 1.2.3"

    settings = (("approval_policy", "never"),)

    def read_settings(
        path: Path, received_config: HarnessConfig
    ) -> tuple[tuple[str, str], ...]:
        events.append("settings")
        settings_inputs.append((path, received_config))
        return settings

    resolver = CodexCliBindingResolver(
        resolve_executable=resolve_executable,
        probe_version=probe_version,
        read_effective_settings=read_settings,
        runner_version=lambda: "0.1.0",
    )

    # When
    binding = resolver.resolve(config)

    # Then
    assert binding == CliBinding(
        executable_path=executable_path,
        cli_version="codex 1.2.3",
        runner_version="0.1.0",
        effective_settings=settings,
        quota_scope=None,
    )
    assert binding.executable_path is executable_path
    assert binding.effective_settings is settings
    assert events == ["resolve", "version", "settings"]
    assert probed_paths == [executable_path]
    assert probed_paths[0] is executable_path
    assert settings_inputs[0][0] is executable_path
    assert settings_inputs[0][1] is config


def test_binding_propagates_probe_failure_without_reading_settings_or_retrying() -> (
    None
):
    # Given
    config, _, _, _, _ = plan_and_inputs()
    failure = RuntimeError("version probe failed")
    events: list[str] = []
    probed_paths: list[Path] = []

    def resolve_executable() -> Path:
        events.append("resolve")
        return Path("/verified/codex")

    def probe_version(path: Path) -> str:
        events.append("probe")
        probed_paths.append(path)
        raise failure

    def read_settings(
        path: Path, received_config: HarnessConfig
    ) -> tuple[tuple[str, str], ...]:
        events.append("settings")
        raise AssertionError("settings must not be read after a failed probe")

    resolver = CodexCliBindingResolver(
        resolve_executable=resolve_executable,
        probe_version=probe_version,
        read_effective_settings=read_settings,
        runner_version=lambda: "0.1.0",
    )

    # When
    with pytest.raises(RuntimeError, match="version probe failed") as raised:
        resolver.resolve(config)

    # Then
    assert raised.value is failure
    assert events == ["resolve", "probe"]
    assert probed_paths == [Path("/verified/codex")]


def test_request_builder_forwards_frozen_context_and_staged_path_in_order() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    staged_path = evidence.model_instructions_file
    events: list[str] = []
    observed_inputs: list[BuilderInputs] = []
    request = AttemptRequest(
        argv=("/bin/codex", "--stubbed"),
        cwd=plan.repository_root,
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        grace_seconds=config.grace_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
    )

    def effective_call_id(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        events.append("identity")
        observed_inputs.append((
            received_plan,
            received_call,
            received_binding,
            received_staged_path,
            received_config,
        ))
        return "call-1"

    def build_attempt_request(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> AttemptRequest:
        events.append("request")
        observed_inputs.append((
            received_plan,
            received_call,
            received_binding,
            received_staged_path,
            received_config,
        ))
        return request

    builder = CodexAttemptRequestBuilder(
        effective_call_id=effective_call_id,
        build_attempt_request=build_attempt_request,
    )

    # When
    effective_call = builder.build(plan, call, binding, evidence, config)

    # Then
    assert effective_call.run_id is plan.run_id
    assert effective_call.call_id == "call-1"
    assert effective_call.planned_call is call
    assert effective_call.request is request
    assert events == ["identity", "request"]
    assert len(observed_inputs) == 2
    assert_builder_inputs(observed_inputs[0], plan, call, binding, staged_path, config)
    assert_builder_inputs(observed_inputs[1], plan, call, binding, staged_path, config)
    assert observed_inputs[0][1].prompt is call.prompt
    assert observed_inputs[0][3] is staged_path
    assert observed_inputs[1][3] is staged_path


def test_request_builder_forwards_no_instruction_path_when_unconfigured() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs(with_instructions=False)
    request = AttemptRequest(
        argv=("/bin/codex",),
        cwd=plan.repository_root,
        timeout_seconds=config.timeout_seconds,
        cleanup_timeout_seconds=config.cleanup_timeout_seconds,
        grace_seconds=config.grace_seconds,
        output_limit_bytes=config.output_limit_bytes,
        stdin="devnull",
    )
    identity_paths: list[Path | None] = []
    request_paths: list[Path | None] = []

    def effective_call_id(
        frozen_plan: FrozenPlan,
        planned_call: PlannedCall,
        cli_binding: CliBinding,
        staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        identity_paths.append(staged_path)
        return "call-with-default-instructions"

    def build_attempt_request(
        frozen_plan: FrozenPlan,
        planned_call: PlannedCall,
        cli_binding: CliBinding,
        staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> AttemptRequest:
        request_paths.append(staged_path)
        return request

    builder = CodexAttemptRequestBuilder(
        effective_call_id=effective_call_id,
        build_attempt_request=build_attempt_request,
    )

    # When
    effective_call = builder.build(plan, call, binding, evidence, config)

    # Then
    assert plan.instructions_file is None
    assert config.instructions_file_path is None
    assert evidence.model_instructions_file is None
    assert identity_paths == [None]
    assert request_paths == [None]
    assert request.argv == ("/bin/codex",)
    assert effective_call.call_id == "call-with-default-instructions"
    assert effective_call.request is request


def test_request_builder_propagates_identity_failure_without_request_retry() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    failure = RuntimeError("identity unavailable")
    events: list[str] = []

    def effective_call_id(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        events.append("identity")
        raise failure

    def build_attempt_request(
        received_plan: FrozenPlan,
        received_call: PlannedCall,
        received_binding: CliBinding,
        received_staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> AttemptRequest:
        events.append("request")
        raise AssertionError("request must not be built after identity failure")

    builder = CodexAttemptRequestBuilder(
        effective_call_id=effective_call_id,
        build_attempt_request=build_attempt_request,
    )

    # When
    with pytest.raises(RuntimeError, match="identity unavailable") as raised:
        builder.build(plan, call, binding, evidence, config)

    # Then
    assert raised.value is failure
    assert events == ["identity"]


def test_outcome_classifier_forwards_only_one_settled_evidence_value() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    evidence = settled_evidence(config)
    assessment = RetryAssessment(
        retry_class="unknown",
        classification_basis=None,
        no_result_basis="present_or_unknown",
        diagnostic="Codex classifier contract is not verified",
    )
    calls: list[AttemptEvidence] = []

    def assess_settled_evidence(received: AttemptEvidence) -> RetryAssessment:
        calls.append(received)
        return assessment

    classifier = CodexOutcomeClassifier(assess_settled_evidence=assess_settled_evidence)

    # When
    result = classifier.assess(evidence)

    # Then
    assert result is assessment
    assert calls == [evidence]
    assert calls[0] is evidence


def test_default_codex_leaf_operations_fail_visibly() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()
    settled = settled_evidence(config)
    resolver = CodexCliBindingResolver()
    builder = CodexAttemptRequestBuilder()
    classifier = CodexOutcomeClassifier()

    # When
    with pytest.raises(NotImplementedError) as resolver_error:
        resolver.resolve(config)
    with pytest.raises(NotImplementedError) as builder_error:
        builder.build(plan, call, binding, evidence, config)
    with pytest.raises(NotImplementedError) as classifier_error:
        classifier.assess(settled)

    # Then
    assert resolver_error.value.args == (
        "Codex executable discovery is not implemented",
    )
    assert builder_error.value.args == ("effective-call identity is not implemented",)
    assert classifier_error.value.args == (
        "Codex outcome signal recognition is not implemented",
    )


def test_default_settings_reader_runs_after_version_probe() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    executable_path = Path("/resolved/codex")
    events: list[str] = []
    probed_paths: list[Path] = []

    def probe_version(path: Path) -> str:
        events.append("version")
        probed_paths.append(path)
        return "codex 1.2.3"

    def resolve_executable() -> Path:
        events.append("resolve")
        return executable_path

    resolver = CodexCliBindingResolver(
        resolve_executable=resolve_executable,
        probe_version=probe_version,
    )

    # When
    with pytest.raises(NotImplementedError) as raised:
        resolver.resolve(config)

    # Then
    assert events == ["resolve", "version"]
    assert probed_paths == [executable_path]
    assert probed_paths[0] is executable_path
    assert raised.value.args == (
        "Codex effective-settings discovery is not implemented",
    )


def test_default_request_operation_fails_after_injected_identity() -> None:
    # Given
    config, plan, call, binding, evidence = plan_and_inputs()

    def effective_call_id(
        plan: FrozenPlan,
        call: PlannedCall,
        binding: CliBinding,
        staged_path: Path | None,
        received_config: HarnessConfig,
    ) -> str:
        return "call-1"

    builder = CodexAttemptRequestBuilder(effective_call_id=effective_call_id)

    # When
    with pytest.raises(NotImplementedError) as raised:
        builder.build(plan, call, binding, evidence, config)

    # Then
    assert raised.value.args == (
        "Codex argv and request construction are not implemented",
    )


def test_classifier_propagates_failure_without_retrying() -> None:
    # Given
    config, _, _, _, _ = plan_and_inputs()
    evidence = settled_evidence(config)
    failure = RuntimeError("classification failed")
    calls: list[AttemptEvidence] = []

    def assess_settled_evidence(received: AttemptEvidence) -> RetryAssessment:
        calls.append(received)
        assert received is evidence
        raise failure

    classifier = CodexOutcomeClassifier(assess_settled_evidence=assess_settled_evidence)

    # When
    with pytest.raises(RuntimeError, match="classification failed") as raised:
        classifier.assess(evidence)

    # Then
    assert raised.value is failure
    assert calls == [evidence]
    assert calls[0] is evidence
